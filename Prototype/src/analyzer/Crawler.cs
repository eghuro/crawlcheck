using System;
using CrawlcheckPrototype.Proxy;
using CrawlcheckPrototype.Report;

namespace CrawlcheckPrototype
{
	namespace Analyzer{
		public class Crawler
		{
			public Crawler ()
			{
			}

			private Finding getLinkFromReport();
			public HttpRequest generateCrawlingRequest();
		}
	}
}

