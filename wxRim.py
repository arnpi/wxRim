#!/usr/bin/env python
# -*- coding:Utf8 -*-
# arnpi@gmx.com
# Date: 26/03/2013
VERSION = 0.1 
PROGRAMME = "wxRIM"

"""
wxRIM
    Lecteur pour une web radio parisienne
    Mode graphique
    Affiche la webcam de la page d'accueil de la radio
    Utilise GStreamer pour lire le flux
    Utilise Wx pour l'interface graphique
    Affiche le forum de la radio dans sa version WAP
    TODO: Enregistrement du flux mp3
"""
# Aide GST python trouvée sur: http://codeboje.de/playing-mp3-stream-python/

import pygst
pygst.require("0.10")
import gst
import wx
import wx.html
import threading
import time
import httplib, urllib
import webbrowser
import tempfile
import os
import re

# CONSTANTES
print "Déclaration des constantes"
WEBCAMURL = 'http://www.icietmaintenant.com/01.jpg'
STREAMADDRESS = 'http://radio.rim952.fr:8000/stream.mp3'
WAPACCESS = "http://icietmaintenant.fr/SMF/index.php?wap2"
URLICON = "http://icietmaintenant.com/favicon.ico"
TEMP_DIR = tempfile.gettempdir() + os.sep
RADIONAME = "Ici et Maintenant 95.2 Fm"
TELEPHONE = "08 92 23 95 20 (34cts/mn)"
USTREAM = 'http://icietmaintenant.com/TimeUstream.htm'

###########################################################

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        print "Constructeur MainWindow"
        self.sHrefActuel = WAPACCESS
        self.bPause = False

        #
        wx.Frame.__init__(self, parent, title=title, size=(-1,-1))

        # msg du forum
        print "Récupération des messages du forum"
        self.forumWindow = wx.html.HtmlWindow(self)
        if "gtk2" in wx.PlatformInfo:
            self.forumWindow.SetStandardFonts()
        self.hideStatut = False
        self.forumWindow.Show(True)
        self.forumStatus = True
        try:
            htmlPageWap = urllib.urlopen(self.sHrefActuel).read().decode('iso-8859-1')
        except Exception:
            htmlPageWap = "Erreur"
        self.forumWindow.SetPage(htmlPageWap)
        self.forumWindow.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OnLinkClicked)

        # A Statusbar in the bottom of the window
        print "Création de la barre de statut"
        self.txtStatusBar = self.CreateStatusBar()

        # icones
        print "Téléchargement de l'icone"
        try:
            urllib.urlretrieve(URLICON,TEMP_DIR + 'favicon.ico')
            # icone barre des taches
            print "Icone barre des taches"
            self.imgIco = wx.Icon(TEMP_DIR + "favicon.ico", wx.BITMAP_TYPE_ICO)
            self.SetIcon(self.imgIco)
            #icone systray
            print "Icone systray"
            self.icoSystray = wx.TaskBarIcon()
            wx.TaskBarIcon.__init__(self.icoSystray)
            self.icoSystray.SetIcon(self.imgIco)
            self.icoSystray.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)
            self.icoSystray.Bind(wx.EVT_TASKBAR_RIGHT_DOWN, self.on_right_down)
            self.icoSystraymenu=wx.Menu()
            self.icoSystraymenu.Append(wx.ID_EXIT, "Close")
            self.icoSystraymenu.Bind(wx.EVT_MENU, self.Quit, id=wx.ID_EXIT)
        except Exception:
            print "Erreur pendant le téléchargement de l'icone'"

        # 1ere capture webcam
        try:
            print "1ère capture webcam"
            urllib.urlretrieve(WEBCAMURL, TEMP_DIR + '01.jpg')
            self.imgWebcam = wx.Image(TEMP_DIR + "01.jpg", wx.BITMAP_TYPE_JPEG)
            self.webcamPanel  = wx.Panel(self, -1, (1, 1), (-1, -1), style = wx.SUNKEN_BORDER)
            self.imgWebcamBmp = self.imgWebcam.ConvertToBitmap()
            self.webcamWindow = wx.StaticBitmap(parent = self.webcamPanel, bitmap = self.imgWebcamBmp)
            sizerImg = wx.BoxSizer()
            sizerImg.Add(item=self.webcamWindow, proportion=0, flag=wx.CENTRE, border=0)
            self.SetSizerAndFit(sizerImg)
        except Exception:
            print "Erreur pendant le téléchargement de la webcam\nFin du programme ..."
            exit()

        # timer refresh auto
        print"Timer refresh auto"
        self.timerRefresh = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.Refresh, self.timerRefresh)
        self.timerRefresh.Start(60000)

        # demarrage du stream
        print "Démarrage du stream"
        self.uriStream = STREAMADDRESS
        self.streamPlayer = gst.element_factory_make("playbin", "player")
        self.streamPlayer.set_property('uri', self.uriStream)
        self.streamPlayer.set_state(gst.STATE_PLAYING)
        print "Stream Démarré"
        self.txtStatusBar.SetStatusText(u"08 92 23 95 20 (34cts/mn) - Playing ...")

        # Interface
        print "Création de l'interface"
        self.buttons2 = wx.Button(self, 1, 'Démarrer')
        self.buttons3 = wx.Button(self, 2, 'Arrêter')
        self.buttons4 = wx.ToggleButton(self, 7, 'Pause')
        self.buttons5 = wx.Button(self, 3, 'Rafraîchir')
        self.buttons6 = wx.Button(self, 4, 'Enregistrer')
        self.buttons7 = wx.Button(self, 5, 'Ustream')
        self.buttons8 = wx.Button(self, 6, 'Quitter')
        self.buttons9 = wx.Button(self, 8, 'Forum')
        self.Bind(wx.EVT_BUTTON, self.Play, id=1)
        self.Bind(wx.EVT_BUTTON, self.Stop, id=2)
        self.Bind(wx.EVT_BUTTON, self.Refresh, id=3)
        self.Bind(wx.EVT_BUTTON, self.Record, id=4)
        self.Bind(wx.EVT_BUTTON, self.Ustream, id=5)
        self.Bind(wx.EVT_BUTTON, self.OnLinkClicked, id=9)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.Pause, id=7)
        self.Bind(wx.EVT_BUTTON, self.Quit, id=6)
        self.Bind(wx.EVT_BUTTON, self.Forum, id=8)
        self.blockButton1 = wx.BoxSizer(wx.HORIZONTAL)
        self.blockButton2 = wx.BoxSizer(wx.HORIZONTAL)
        self.blockButton1.Add(self.buttons2, 1, wx.EXPAND)
        self.blockButton1.Add(self.buttons3, 1, wx.EXPAND)
        self.blockButton1.Add(self.buttons4, 1, wx.EXPAND)
        self.blockButton1.Add(self.buttons5, 1, wx.EXPAND)
        self.blockButton2.Add(self.buttons6, 1, wx.EXPAND)
        self.blockButton2.Add(self.buttons7, 1, wx.EXPAND)
        self.blockButton2.Add(self.buttons8, 1, wx.EXPAND)
        self.blockButton2.Add(self.buttons9, 1, wx.EXPAND)
        self.blockButtons = wx.BoxSizer(wx.VERTICAL)
        self.blockButtons.Add(self.blockButton1, 1, wx.CENTRE)
        self.blockButtons.Add(self.blockButton2, 1, wx.CENTRE)
        # Sizers
        self.sizerHorizontal = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerVertical = wx.BoxSizer(wx.VERTICAL)
        self.sizerVertical.Add(self.webcamPanel, 0, wx.CENTRE)
        self.sizerVertical.Add(self.blockButtons, 0, wx.CENTRE)
        self.sizerHorizontal.Add(self.sizerVertical, 0, wx.CENTRE)
        self.sizerHorizontal.Add(self.forumWindow, 0, wx.EXPAND)
        #Layout sizers
        self.SetSizer(self.sizerHorizontal)
        self.SetAutoLayout(-1)
        self.sizerHorizontal.Fit(self)
        self.Show()

        # Empechement de l'apparition du forum a l'ouverture'
        print "Empechement de l'apparition du forum a l'ouverture"
        self.Forum(self)

        # empecher le redimensionnement
        print "Empecher le redimensionnement"
        self.SetSizeHints(self.GetSize().x,self.GetSize().y,self.GetSize().x,self.GetSize().y );

    def on_right_down(self, event):
        print "Clique droit"
        self.PopupMenu(self.icoSystraymenu)

    def on_left_down(self, event):
        print "Clique gauche"
        if self.hideStatut == False:
            self.Hide()
            self.hideStatut = True
        else:
            self.Show()
            self.hideStatut = False

    def OnLinkClicked(self, event):
        print "Lien cliqué"
        print self.sHrefActuel
        self.sHrefActuel = event.GetLinkInfo().GetHref()
        print self.sHrefActuel
        self.Refresh(self)

    def Forum(self, event):
        print "Toggle forum"
        self.SetSizeHints(-0,-0);
        if self.forumStatus == False:
            self.forumWindow.Show(True)
            self.SetSizer(self.sizerHorizontal)
            self.SetAutoLayout(-1)
            self.sizerHorizontal.Fit(self)
            self.Show()
            self.forumStatus = True
            print "Le forum est Affiché"
        else:
            self.forumWindow.Show(False)
            self.SetSizer(self.sizerHorizontal)
            self.SetAutoLayout(-1)
            self.sizerHorizontal.Fit(self)
            self.Show()
            self.forumStatus = False
            print "Le forum est Masqué"
        self.SetSizeHints(self.GetSize().x,self.GetSize().y,self.GetSize().x,self.GetSize().y );

    def Play(self, event):
        print "Démarrage du stream"
        self.streamPlayer.set_state(gst.STATE_NULL)
        self.streamPlayer.set_state(gst.STATE_PLAYING)
        self.txtStatusBar.SetStatusText(TELEPHONE + u" - En cours ...")
        print "Stream démarré"

    def Pause(self, event):
        print "Toggle pause"
        if self.bPause == False:
            self.streamPlayer.set_state(gst.STATE_PAUSED)
            self.bPause = True
            self.txtStatusBar.SetStatusText(TELEPHONE + u" - En pause ...")
            print "En pause"
        else:
            self.streamPlayer.set_state(gst.STATE_PLAYING)
            self.bPause = False
            self.txtStatusBar.SetStatusText(TELEPHONE + u" - En cours ...")
            print "En cours"

    def Stop(self, event):
        print "Arrêter stream"
        self.streamPlayer.set_state(gst.STATE_NULL)
        self.txtStatusBar.SetStatusText(TELEPHONE + u" - Stoppé ...")

    def Refresh(self, event):
        print "Rafraichissement ..."
        self.SetSizeHints(-0,-0);
        print "Téléchargement de la webcam ..."
        try:
            urllib.urlretrieve(WEBCAMURL, TEMP_DIR + '01.jpg')
            self.imgWebcam = wx.Image(TEMP_DIR + "01.jpg", wx.BITMAP_TYPE_JPEG)
            self.imgWebcamBmp = self.imgWebcam.ConvertToBitmap()
            print "Terminé"
        except Exception:
            print "IMG 320x240 ERROR"
        self.size = self.imgWebcamBmp.GetWidth(), self.imgWebcamBmp.GetHeight()
        self.webcamWindow = wx.StaticBitmap(parent = self.webcamPanel, bitmap = self.imgWebcamBmp)
        try:
            print "Rafraiîchissement de la page du forum"
            htmlPageWap = urllib.urlopen(self.sHrefActuel).read().decode('iso-8859-1')
            self.forumWindow.SetPage(htmlPageWap)
            print "Terminé"
        except Exception:
            print "Erreur récupération forum"
            self.forumWindow.SetPage("Erreur")

        self.SetSizer(self.sizerHorizontal)
        self.SetAutoLayout(-1)
        self.sizerHorizontal.Fit(self)
        if self.forumStatus == True:
            self.Show()
        self.SetSizeHints(self.GetSize().x,self.GetSize().y,self.GetSize().x,self.GetSize().y );

    def Record(self, event):
        print "Not Done"

    def Ustream(self, event):
        print "Ouvrir Ustream"
        webbrowser.open(USTREAM)

    def Quit(self, event):
        exit()

app = wx.App(False)
frame = MainWindow(None, RADIONAME)
app.MainLoop()
