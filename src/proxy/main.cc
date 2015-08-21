// Copyright 2015 Alexandr Mansurov

#include <string.h>
#include <signal.h>
#include <sys/wait.h>
#include <cstdlib>
#include <memory>
#include <libxml++/libxml++.h>
#include "./ProxyConfiguration.h"
#include "./db.h"
#include "./RequestStorage.h"
#include "./ServerAgent.h"
#include "./ClientAgent.h"

int main(int argc, char ** argv) {
  if (argc == 2) {  // jmeno konfigurak
    std::string config(argv[1]);

    try {
      ConfigurationParser parser;
      parser.set_substitute_entities(true);
      parser.parse_file(config);

      if (parser.versionMatch()) {
        HelperRoutines::info("Parsed configuration, creating ProxyConfiguration sharedptr");

        std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(parser.getProxyConfiguration()));
        HelperRoutines::info("Parsed configuration");
        HelperRoutines::info("Created db, creating RequestStorage sharedptr");
        RequestStorage* rs = new RequestStorage(parser.getDatabaseConfiguration(), static_cast<std::size_t>(pconf->getOutPoolCount()));

        HelperRoutines::info("Created RequestStorage, creating RS lock");
        pthread_mutex_t * rs_lock ((pthread_mutex_t *)malloc(sizeof(pthread_mutex_t)));
        int e = pthread_mutex_init(rs_lock, NULL);
        if (e != 0) {
          HelperRoutines::error("Create request storage mutex");
        }
        HelperRoutines::info("Created RS lock");
        std::ostringstream oss;
        oss << "RS lock {" << rs_lock << "}";
        HelperRoutines::info(oss.str());

        HelperRoutines::info("Creating server agent");
        ServerAgent * sa = new ServerAgent(pconf, rs, rs_lock);

        HelperRoutines::info("Created ServerAgent, creating client agent");
        ClientAgent * ca = new ClientAgent(pconf, rs, rs_lock);

        //zablokovat signaly: SIGHUP, SIGINT, <SIGTERM>, mozna SIGQUIT, SIGABRT
        //forky
        int pid0, pid1;
        switch (pid0 = fork()) {
        case -1: HelperRoutines::error("Fork server"); break;
        case 0: // child
          HelperRoutines::info("ServerAgent");
          HelperRoutines::info("Start SA");
          sa->start();
          sa->stop();
          delete sa;
          break;
        default:
          switch (pid1 = fork()) {
          case -1: HelperRoutines::error("Fork client"); break;
          case 0: //child
            HelperRoutines::info("ClientAgent");

            HelperRoutines::info("Start CA");
            ca->start();
            ca->stop();
            delete ca;
            break;
          default: //parent
            HelperRoutines::info("Service process");

            //odblokovat signaly
            //zachytit signaly (viz vyse)

            wait(NULL); // wait for all children processes to finish
            HelperRoutines::info("Child processes finished, cleaning up");
            delete ca;
            delete sa;
            pthread_mutex_destroy(rs_lock);
            delete rs;
            return EXIT_SUCCESS;
            }
          break;
        }
      } else {
        return EXIT_FAILURE;
      }
    } catch(const xmlpp::exception& ex) {
      HelperRoutines::error("libxml++ exception: ", ex.what());
    }
  } else {
    std::cout << "Usage: "<< argv[0] << " <configuration.xml>" << std::endl;
    return EXIT_FAILURE;
  }
}
