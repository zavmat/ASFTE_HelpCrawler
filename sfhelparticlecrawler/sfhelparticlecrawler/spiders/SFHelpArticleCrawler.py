from urllib.parse import urlparse
import scrapy
from scrapy import Item, Field


# Item to store crawled data
class PageItem(Item):
    url = Field()  # url of the element extracted
    referrer_url = Field()  # url which was crawled before the current url
    data_source = Field()  # source of data (html/pdf/etc.) for extensibility
    intra_doc_depth = Field()  # relative depth of the item (e.g.: depth of div(in parsed html) or table of content level (aria-level))
    plain_text = Field()  # extracted text without processing and cleansing


class SFHelpArticleCrawler(scrapy.Spider):

    BASE_URL = 'https://help.salesforce.com'
    name = 'helparticles'
    allowed_domains = ['help.salesforce.com']

    #Initite crawl from documentation landing page (help map)
    def start_requests(self):
        yield scrapy.Request('https://help.salesforce.com/articleView?id=salesforce_help_map.htm&type=5',
                             self.parse_landing)

    # Parse the Documentation landing page (salesforce_help_map)
    def parse_landing(self, response):
        # Create a crawl request for all help pages and process them
        getone = True
        for href in response.xpath('//a[@class=\'tile-title\']/@href').getall():
            if (not len(urlparse(href).netloc) > 0):
                absolute_url = self.BASE_URL + href
                yield scrapy.Request(absolute_url, self.parse_helpdoc)


    def parse_helpdoc(self, response):
        # Extract TOC
        page = response.xpath('//div[@class=\'toc-content\']/ul/li')
        getone = True
        for elem in page:
            depth = elem.attrib['aria-level']
            link = elem.xpath('.//a').attrib['href']
            text = elem.xpath('.//a/text()').get()
            absolute_url = self.BASE_URL + link
            yield scrapy.Request(absolute_url, self.parse_article, cb_kwargs={'depth': depth})

    def parse_article(self, response, depth):

        #Extract title of help(documentation) article
        title = response.xpath(
            '//head/title/text()').get()

        #Extract short summary of help(documentation) article

        summary = ''.join(response.xpath('//div[@id=\'content\']/p/text()').getall())

        page = PageItem()
        page['url'] = response.url
        page['referrer_url'] = response.request.headers.get('Referer', None)
        page['data_source'] = 'html'
        page['intra_doc_depth'] = depth
        page['plain_text'] = title + '. ' + summary

        yield page
