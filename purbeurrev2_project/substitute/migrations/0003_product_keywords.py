# Generated by Django 3.1.7 on 2021-03-22 13:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('substitute', '0002_auto_20210319_1032'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='keywords',
            field=models.CharField(default='produit', max_length=500),
            preserve_default=False,
        ),
    ]
