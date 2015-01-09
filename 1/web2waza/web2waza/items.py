from scrapy.item import Item, Field
class Web2WazaItem(Item):
    typeid = Field()
    fromurl = Field()

    subject = Field()
    tags = Field()
    message = Field()
    desc = Field()
    cover_name = Field()
    cover_info = Field()

    artile_id_key = Field()
    keytype = Field()
    ori_web = Field()

    image_urls = Field()
    images = Field()

    iframe = Field()
