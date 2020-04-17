# Generated by Django 3.0.5 on 2020-04-17 01:27

import bakerydemo.locations.models
from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0004_auto_20190912_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='locationpage',
            name='test_a',
            field=wagtail.core.fields.StreamField([('ip_address', bakerydemo.locations.models.IPAddressBlock()), ('title', wagtail.core.blocks.CharBlock(label='Title', required=True)), ('content', wagtail.core.blocks.RichTextBlock(label='Content', required=False))], blank=True, verbose_name='Map Foo'),
        ),
    ]
