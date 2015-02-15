using System;
using CrawlcheckPrototype.Proxy;
using CrawlcheckPrototype.Report;

namespace CrawlcheckPrototype
{
	namespace Analyzer{
		public class Dispatcher
		{
			public Dispatcher ()
			{
			}

			public void registerValidator(IValidator v);

			public void handleResponse(HttpResponse r);

			private void passResponseToAnalyzer(HttpResponse r);
			public void handleFinding (Finding f);
			private void storeFindingToReport(Finding f);
		}
	}
}

