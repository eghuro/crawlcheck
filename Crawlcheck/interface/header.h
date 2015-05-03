/*
 * header.h
 *
 *  Created on: 19 Jan 2015
 *      Author: alex
 */

#ifndef HEADER_H_
#define HEADER_H_
#include<string>
#include<memory>

namespace crawlcheck{
	namespace net{
		typedef int addr_t;
		typedef std::string data_t;
		class HttpEnvelope {
		public:
			HttpEnvelope(const addr_t src, const addr_t dst, const data_t & data):src_l(src), dst_l(dst), data_l(data) {
			}

			inline addr_t getSrc() const {
				return src_l;
			}

			inline addr_t getDst() const {
				return dst_l;
			}

			const inline data_t & getData() const {
				return data_l;
			}
		private:
			const addr_t src_l;
			const addr_t dst_l;
			const data_t & data_l;
		};

		class HttpEnvelopeFactory {
		public:
			static HttpEnvelopeFactory & Instance() {
				if (!pInstance_) {
					pInstance_ = std::unique_ptr<HttpEnvelopeFactory>(new HttpEnvelopeFactory);
				}
				return pInstance_;
			}
		private:
			explicit HttpEnvelopeFactory();//prevent new factory
			HttpEnvelopeFactory(const HttpEnvelopeFactory&) = delete;//prevent copy
			HttpEnvelopeFactory& operator=(const HttpEnvelopeFactory&) = delete;//prevent assignment
			~HttpEnvelopeFactory();

			static std::unique_ptr<HttpEnvelopeFactory> pInstance_;
		};
	};

	namespace data{

	};
};

#endif /* HEADER_H_ */
