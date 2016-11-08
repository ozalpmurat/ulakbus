# -*-  coding: utf-8 -*-
# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
#
from zengine.views.crud import CrudView
from zengine.forms import JsonForm
from zengine.forms import fields
from zengine.lib.translation import gettext as _
from ulakbus.lib.common import parola_kontrolleri
from ulakbus.views.common.profil_sayfasi_goruntuleme import mesaj_goster


class ParolaDegistir(CrudView):
    """
    Kullanıcıların parolalarını değiştirebilmelerini sağlar.
    """

    def yeni_parola_girisi(self):
        """
        Parola değişikliği ekranını oluşturur. Kullanıcı parolasını değiştirirken hata yaparsa
        (8 karakterden az parola seçimi gibi), hata kontrol edildikten sonra yine bu ekranda
        gösterilir.

        """
        try:
            if self.current.task_data['msg']:
                mesaj_goster(self, _(u'Parola Hatalı'))
        except KeyError:
            pass

        _form = JsonForm(current=self.current, title=_(u'Parola Değiştirme'))
        _form.help_text = _((u"Kendi güvenliğiniz ve sistem güvenliği için yeni oluşturacağınız parola:\n"
                             u"\n"
                             u"* Türkçe karakter içermemeli,\n"
                             u"* 8 karakterden büyük olmalı,\n"
                             u"* En az bir küçük harf, bir büyük harf, bir sayı ve bir özel karakter içermeli,\n"
                             u"* Eski şifrenizle aynı olmamalıdır.\n"
                             u"* Özel karakterler = [\* & ^ % $ @ ! ? . : / > < ; ]\n"
                             u"* Örnek parola = Ulakbüs3\*\n"))

        _form.eski_parola = fields.String(_(u"Şu an kullandığınız parolanızı giriniz."))
        _form.yeni_parola = fields.String(_(u"Yeni parolanızı giriniz."))
        _form.yeni_parola_tekrar = fields.String(_(u"Yeni parolanızı tekrar giriniz."))
        _form.degistir = fields.Button(_(u"Parola Değiştir"))
        self.form_out(_form)

    def yeni_parola_kontrol(self):
        """
        Girilen parolalar önce Cache'e atılır. Ardından parola kontrol methodlarına gönderilir.
        Eğer parola kontrol methodlarından geçerse parola kaydetme adımına gidilir. Eğer parola
        değişikliğinde bir hata olursa hata mesajı ile bir önceki adıma gidilip hata gösterilir
        ve parola değişikliğini yeniden denemesi istenir.

        """
        eski_parola = self.input['form']['eski_parola']
        yeni_parola = self.input['form']['yeni_parola']
        yeni_parola_tekrar = self.input['form']['yeni_parola_tekrar']
        kullanici = self.current.user

        parola_uygunluk, hata_mesaji = parola_kontrolleri(yeni_parola, yeni_parola_tekrar, kullanici, eski_parola)

        self.current.task_data['uygunluk'] = parola_uygunluk

        if not parola_uygunluk:
            self.current.task_data['msg'] = hata_mesaji

    def yeni_parola_kaydet(self):
        """
        Cache'e atılan parolalar güvenlik nedeniyle tekrardan parola kontrol methodlarına
        gönderilir. Kontrolden geçerse parola değiştirilir ve işlem başarılı mesajı yaratılır.
        Eğer kontrolden geçmezse ki bu beklenmeyen bir durumdur. Beklenmeyen hata adımına gidilir
        ve hata gösterilir.

        """
        eski_parola = self.input['form']['eski_parola']
        yeni_parola = self.input['form']['yeni_parola']
        yeni_parola_tekrar = self.input['form']['yeni_parola_tekrar']
        kullanici = self.current.user
        self.current.task_data['islem'] = False

        parola_uygunluk, hata_mesaji = parola_kontrolleri(yeni_parola, yeni_parola_tekrar, kullanici, eski_parola)

        if parola_uygunluk:
            self.current.user.set_password(yeni_parola)
            self.current.user.save()
            self.current.task_data['islem'] = True
            self.current.task_data['msg'] = None
            self.current.task_data['islem_mesaji'] = _(u"""Parolanız başarıyla değiştirildi. Çıkış
                                                                 yapıp yeni parolanızla giriş yapabilirsiniz""")
