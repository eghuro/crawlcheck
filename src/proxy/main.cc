// Copyright 2015 Alexandr Mansurov

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
        HelperRoutines::info("Parsed configuration, creating Database sharedptr");
        std::shared_ptr<Database> db(new Database(parser.getDatabaseConfiguration()));
        HelperRoutines::info("Created db, creating RequestStorage sharedptr");
        RequestStorage* rs = new RequestStorage(db);

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

        int pid;
        switch (pid = fork()) {
        case -1: HelperRoutines::error("Fork client & server"); break;
        case 0:
          HelperRoutines::info("ClientAgent");
          HelperRoutines::info("Start CA");
          ca->start();
          HelperRoutines::info("Stop CA");
          ca->stop();
          HelperRoutines::info("Stopped, delete CA!");
          delete ca;
          HelperRoutines::info("Leaving CA process, bye");

          break;
         default:
          HelperRoutines::info("ServerAgent");
          HelperRoutines::info("Start SA");
          sa->start();
          HelperRoutines::info("Leaving SA process, bye");
          break;
        }

        // bezi sada vlaken, ktere konaji nejakou cinnost
        // v destruktorech ClientThread a ServerThread, ktere se spusti z
        // destruktoru ClientAgent resp. ServerAgent se vola pthread_join

        delete rs;

        return EXIT_SUCCESS;
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
