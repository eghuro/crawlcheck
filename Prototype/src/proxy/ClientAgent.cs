using System;

namespace CrawlcheckPrototype
{
	namespace Proxy{
		public class ClientAgent
		{
			private Processor processor;

			public ClientAgent ()
			{
			}

			private void listenForRequest () ;
			private HttpRequest generateRequest ();

			private void passRequest(HttpRequest r) {
				processor.handleProxyRequest (r);
			}

			public void passResponse (HttpResponse r);
		}
	}
}

