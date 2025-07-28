from django.contrib import admin
from . import models
from .utils import generate_static_list_search_html, generate_static_sku_detail_html


class GoodsCategoryAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_list_search_html()

    def delete_model(self, request, obj):
        obj.delete()
        generate_static_list_search_html()


class GoodsChannelAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_list_search_html()

    def delete_model(self, request, obj):
        obj.delete()
        generate_static_list_search_html()


class SKUAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_sku_detail_html(obj.id)


class SKUImageAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        sku = obj.sku
        if not sku.default_image_url:
            sku.default_image_url = obj.image.url
            sku.save()
        generate_static_sku_detail_html(sku.id)

    def delete_model(self, request, obj):
        obj.delete()
        sku = obj.sku
        generate_static_sku_detail_html(sku.id)

admin.site.register(models.GoodsCategory, GoodsCategoryAdmin)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU, SKUAdmin)
admin.site.register(models.SKUSpecification)
admin.site.register(models.SKUImage, SKUImageAdmin)