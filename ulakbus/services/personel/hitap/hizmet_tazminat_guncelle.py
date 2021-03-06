# -*-  coding: utf-8 -*-

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.

"""HITAP Tazminat Guncelle

Hitap'a personelin Tazminat bilgilerinin guncellemesini yapar.

"""

from ulakbus.services.personel.hitap.hitap_guncelle import HITAPGuncelle


class HizmetTazminatGuncelle(HITAPGuncelle):
    """
    HITAP Guncelleme servisinden kalıtılmış Hizmet Tazminat Bilgi Guncelleme servisi

    """
    HAS_CHANNEL = True

    def handle(self):
        """Servis çağrıldığında tetiklenen metod.

        Attributes:
            service_name (str): İlgili Hitap sorgu servisinin adı
            service_dict (dict): Request yoluyla gelen kayıtlar,
                    HizmetTazminatUpdate servisinin alanlarıyla eşlenmektedir.
                    Filtreden geçecek tarih alanları listede tutulmaktadır.
        """

        self.service_name = 'HizmetTazminatUpdate'
        self.service_dict = {
            'fields': {
                'kayitNo': self.request.payload.get('kayit_no', ''),
                'gorev': self.request.payload.get('gorev', ''),
                'kadrosuzluk': self.request.payload.get('kadrosuzluk', ''),
                'makam': self.request.payload.get('makam', ''),
                'tckn': self.request.payload.get('tckn', ''),
                'temsil': self.request.payload.get('temsil', ''),
                'unvanKod': self.request.payload.get('unvan_kod', ''),
                'tazminatTarihi': self.request.payload.get('tazminat_tarihi', ''),
                'tazminatBitisTarihi': self.request.payload.get('tazminat_bitis_tarihi', ''),
                'kurumOnayTarihi': self.request.payload.get('kurum_onay_tarihi', '')
            },
            'date_filter': ['tazminatTarihi', 'tazminatBitisTarihi', 'kurumOnayTarihi'],
            'required_fields': ['kayitNo', 'tckn', 'unvanKod', 'tazminatTarihi', 'kurumOnayTarihi']
        }
        super(HizmetTazminatGuncelle, self).handle()
