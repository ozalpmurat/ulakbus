# -*-  coding: utf-8 -*-
# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
#
"""Danışman Modülü

İlgili İş Akışlarına ait sınıf ve metotları içeren modüldür.

Dönem bazlı danışman atanmasını sağlayan iş akışını yönetir.

"""

from pyoko import ListNode
from pyoko.db.adapter.db_riak import BlockSave
from pyoko.exceptions import ObjectDoesNotExist
from ulakbus.lib.common import notify
from zengine import forms
from zengine.forms import fields
from zengine.views.crud import CrudView
from ulakbus.models.ogrenci import Donem, DonemDanisman, Okutman
from ulakbus.models.auth import Unit
from ulakbus.views.ders.ders import prepare_choices_for_model
from zengine.lib.translation import gettext as _, gettext_lazy


class DonemDanismanForm(forms.JsonForm):
    """``DonemDanismanAtama`` sınıfı için form olarak kullanılacaktır.

    """

    ileri = fields.Button(gettext_lazy(u"İleri"))


class DonemDanismanListForm(forms.JsonForm):
    class Meta:
        inline_edit = ['secim']

    class Okutmanlar(ListNode):
        secim = fields.Boolean(gettext_lazy(u'Seçim'), type="checkbox")
        ad_soyad = fields.String(gettext_lazy(u'Ad Soyad'))
        key = fields.String(gettext_lazy(u'Key'), hidden=True)

    kaydet = fields.Button(gettext_lazy(u"Kaydet"))


class DonemDanismanAtama(CrudView):
    """Dönem Danışman Atama İş Akışı

    Dönem Danışman Atama, aşağıda tanımlı iş akışı adımlarını yürütür.

    - Bölüm Seç
    - Öğretim Elemanlarını Seç
    - Kaydet
    - Kayıt Bilgisi Göster

     Bu iş akışında kullanılan metotlar şu şekildedir:

     Bölüm Seç:
        Kullanıcının bölüm başkanı olduğu bölümleri listeler.

     Öğretim Elemanlarını Seç:
        Seçilen bölümdeki öğretim elemanları listelenir.

     Kaydet:
        Seçilen öğretim elemanları danışman olarak kaydeder.

     Kayıt Bilgisi Göster:
        Seçilen öğretim elemanları, dönem ve bölüm bilgilerinden oluşturulan kaydın mesajı
        gösterilir.
        Danışmanlara bilgilendirme mesajı gönderilir.
        Bu adımdan sonra iş akışı sona erer.

     Bu sınıf ``CrudView`` extend edilerek hazırlanmıştır. Temel model
     ``DonemDanisman`` modelidir. Meta.model bu amaçla kullanılmıştır.

     Adımlar arası geçiş manuel yürütülmektedir.

    """

    class Meta:
        model = "DonemDanisman"

    def bolum_sec(self):
        """
        Kullanıcının bölüm başkanı olduğu bölümleri listeler.

        """

        _unit = self.current.role.unit
        _form = DonemDanismanForm(current=self, title=_(u"Bölüm Seçiniz"))
        _choices = prepare_choices_for_model(Unit, yoksis_no=_unit.yoksis_no)
        _form.program = fields.Integer(choices=_choices)
        self.form_out(_form)

    def danisman_sec(self):
        """
        Seçilen bölümdeki öğretim elemanları listelenir.

        """

        unit = Unit.objects.get(self.current.input['form']['program'])
        self.current.task_data['unit_yoksis_no'] = unit.yoksis_no
        okutmanlar = Okutman.objects.filter(birim_no=unit.yoksis_no)
        donem = Donem.guncel_donem()
        _form = DonemDanismanListForm(current=self, title=_(u"Okutman Seçiniz"))
        for okt in okutmanlar:
            try:
                DonemDanisman.objects.get(donem=donem, okutman=okt, bolum=unit)
                _form.Okutmanlar(secim=True, ad_soyad='%s %s' % (okt.ad, okt.soyad),
                                 key=okt.key)
            except ObjectDoesNotExist:
                _form.Okutmanlar(secim=False, ad_soyad='%s %s' % (okt.ad, okt.soyad),
                                 key=okt.key)

        self.form_out(_form)
        self.current.output["meta"]["allow_actions"] = False
        self.current.output["meta"]["allow_selection"] = False
        self.current.output["meta"]["allow_add_listnode"] = False

    def danisman_kaydet(self):
        """
        Seçilen öğretim elemanları danışman olarak kaydeder.

        """
        yoksis_no = self.current.task_data['unit_yoksis_no']
        unit = Unit.objects.get(yoksis_no=yoksis_no)
        donem = Donem.guncel_donem()
        danismanlar = self.current.input['form']['Okutmanlar']

        self.current.task_data['okutmanlar'] = []
        with BlockSave(DonemDanisman):
            for danisman in danismanlar:
                if danisman['secim']:
                    key = danisman['key']
                    okutman = Okutman.objects.get(key)
                    DonemDanisman.objects.get_or_create(okutman=okutman, donem=donem, bolum=unit)
                    self.current.task_data['okutmanlar'].append(okutman.key)

    def kayit_bilgisi_ver(self):
        """
        Seçilen öğretim elemanları, dönem ve bölüm bilgilerinden oluşturulan kaydın mesajı
        gösterilir.
        Danışmanlara bilgilendirme mesajı gönderilir.

        """
        yoksis_no = self.current.task_data['unit_yoksis_no']
        unit = Unit.objects.get(yoksis_no=yoksis_no)
        donem = Donem.objects.get(guncel=True)

        self.current.output['msgbox'] = {
            'type': 'info', "title": _(u'Danismanlar Kaydedildi'),
            "msg": _(u'%(donem)s dönemi için %(donem)s programına ait danışman listesi kaydedilmiştir') % {
                'donem': donem, 'unit': unit}}

        title = _(u"Danışman Atama")
        message = _(u"%s dönemi için  danışman olarak atandınız.") % donem
        for okutman_key in self.current.task_data['okutmanlar']:
            okutman = Okutman.objects.get(okutman_key)
            notify(okutman.personel.user if okutman.personel else okutman.harici_okutman.user, message, title)
            print "dslkjk"
