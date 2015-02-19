namespace CrawlcheckPrototype {
  namespace Configurator{
    public class Repository {
       private static readonly Repository INSTANCE = new Repository();
       
       private Repository () {}
       public static Repository getInstance() {
          return INSTANCE;
       }
       
       public String getProperty(String key) {}
       public void loadProperties(String file) {}
    }