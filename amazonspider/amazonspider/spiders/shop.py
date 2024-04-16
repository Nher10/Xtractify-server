from urllib.parse import urljoin

import scrapy


class AmazonSearchProductSpider(scrapy.Spider):
    name = "amazon_search_product"

    custom_settings = {
        "FEEDS": {"searchItem.json": {"format": "json", "overwrite": True}}
    }

    def __init__(self, keyword=None, *args, **kwargs):
        super(AmazonSearchProductSpider, self).__init__(*args, **kwargs)
        self.start_urls = [f"https://www.amazon.com/s?k={keyword}&page=1"]
        self.keyword = keyword
        self.item_count = 0

    def parse(self, response):
        page = response.meta.get("page", 1)

        ## Discover Product URLs
        search_products = response.css(
            "div.s-result-item[data-component-type=s-search-result]"
        )
        for product in search_products:
            relative_url = product.css("h2>a::attr(href)").get()
            product_url = urljoin("https://www.amazon.com/", relative_url).split("?")[0]
            yield scrapy.Request(
                url=product_url,
                callback=self.parse_product_data,
                meta={"page": page},
            )

            self.item_count += 1

            if self.item_count >= 6:
                return

        ## Get All Pages
        if page == 1:
            available_pages = response.xpath(
                '//*[contains(@class, "s-pagination-item")][not(has-class("s-pagination-separator"))]/text()'
            ).getall()

            last_page = available_pages[-1]
            for page_num in range(2, int(last_page)):
                amazon_search_url = (
                    f"https://www.amazon.com/s?k={self.keyword}&page={page_num}"
                )
                yield scrapy.Request(
                    url=amazon_search_url,
                    callback=self.parse,
                    meta={"page": page_num},
                )

    def parse_product_data(self, response):
        feature_bullets = [
            bullet.strip()
            for bullet in response.css("#feature-bullets li ::text").getall()
        ]
        price = response.css('.a-price span[aria-hidden="true"] ::text').get("")
        if not price:
            price = response.css(".a-price .a-offscreen ::text").get("")
        yield {
            "visit": response.url,
            "name": response.css("#productTitle::text").get("").strip(),
            "price": price,
            "image": response.css("div>img::attr(src)").get(),
            "stars": response.css("i[data-hook=average-star-rating] ::text")
            .get("")
            .strip(),
            "rating_count": response.css("div[data-hook=total-review-count] ::text")
            .get("")
            .strip(),
            "feature_bullets": feature_bullets,
        }
