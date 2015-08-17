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
        std::shared_ptr<ProxyConfiguration> pconf(std::make_shared<ProxyConfiguration>(parser.getProxyConfiguration()));
        std::shared_ptr<Database> db(new Database(parser.getDatabaseConfiguration()));
        std::shared_ptr<RequestStorage> rs(new RequestStorage(db));

        ServerAgent server(pconf, rs);
        ClientAgent client(pconf, rs);

        server.start();
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
  }
}
