using System;

namespace CrawlcheckPrototype
{
	namespace Proxy{
		public class Processor
		{
			public Processor ()
			{
			}

			public void handleProxyRequest (HttpRequest r) {
			   HttpResponse response = checkCache(r);
			   if (response != NULL) {
			      passResponseToClient(response);
			   } else {
			      //passRequest - handle data flow correctly
			   }
			}
			public void handleCrawlerRequest (HttpRequest r);
			
			private HttpResponse checkCache (HttpRequest r);
			private void passRequest (HttpRequest r);

			public void handleResponse (HttpResponse r) {
			   cacheResponse(r);
			   passResponseToAnalyzer(r);
			   passResponseToClient(r);
			}
			
			private void cacheResponse (HttpResponse r);
			private void passResponseToClient (HttpResponse r);
			private void passResponseToAnalyzer (HttpResponse r);
		}
	}
}

