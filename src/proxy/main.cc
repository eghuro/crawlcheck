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
        std::cout << "Parsed configuration, creating ProxyConfiguration sharedptr" << std::endl;

        std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(parser.getProxyConfiguration()));
        std::cout << "Parsed configuration, creating Database sharedptr" << std::endl;
        std::shared_ptr<Database> db(new Database(parser.getDatabaseConfiguration()));
        std::cout << "Created db, creating RequestStorage sharedptr" << std::endl;
        std::shared_ptr<RequestStorage> rs(new RequestStorage(db));

        std::cout << "Created RequestStorage, creating server agent" << std::endl;
        ServerAgent server(pconf, rs);
        std::cout << "Created ServerAgent, creating client agent" << std::endl;
        ClientAgent client(pconf, rs);

        std::cout << "Starting server"<<std::endl;
        server.start();
        std::cout << "Starting client"<<std::endl;
        client.start();

        // bezi sada vlaken, ktere konaji nejakou cinnost
        // v destruktorech ClientThread a ServerThread, ktere se spusti z
        // destruktoru ClientAgent resp. ServerAgent se vola pthread_join

        return EXIT_SUCCESS;
      } else {
        return EXIT_FAILURE;
      }
    } catch(const xmlpp::exception& ex) {
      std::cerr << "libxml++ exception: " << ex.what() << std::endl;
      return EXIT_FAILURE;
    }
  } else {
    std::cout << "Usage: "<< argv[0] << " <configuration.xml>" << std::endl;
    return EXIT_FAILURE;
  }
}
