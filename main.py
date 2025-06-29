from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import ButtonBehavior
import os
from functools import partial
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
import pandas as pd
import time

class SistemaPage(Screen):
    pass

class SelecionarPage(Screen):
    pass

class ImageButton(ButtonBehavior, Image):
    pass

class LabelButton(ButtonBehavior, Label):
    pass

class BannerSistema(GridLayout):
    def __init__(self, **kwargs):
        super().__init__()
        self.cols = 3
        
        imagem = kwargs['imagem']
        label = (kwargs['label'])
        meu_aplicativo = App.get_running_app()

        baner = FloatLayout()
        baner_imagem = ImageButton(pos_hint={'right': 1, 'top': 0.85}, size_hint=(1, 0.65), 
                             source=f'icones/{imagem}', on_release=partial(meu_aplicativo.selecionar_sistema, imagem))
        baner_label = LabelButton(text=label, pos_hint={'right': 1, 'top': 0.15}, size_hint=(1, 0.15), 
                                  on_release=partial(meu_aplicativo.selecionar_sistema, imagem))

        baner.add_widget(baner_imagem)
        baner.add_widget(baner_label)

        self.add_widget(baner)

class BannerSelecionar(GridLayout):
    def __init__(self, **kwargs):
        super().__init__()
        
        self.rows = 2

        with self.canvas:
            Color(rgb=(0, 0, 0, 1))
            self.rec = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self.atualizar_rec, size=self.atualizar_rec)

        codigo = kwargs['codigo']

        meu_aplicativo = App.get_running_app()

        banner = FloatLayout()
        baner_label = LabelButton(text=codigo, pos_hint={'right': 0.6, 'top': 0.15}, size_hint=(0.3, 0.15), 
                                  on_release=partial(meu_aplicativo.preencher_codigo, codigo))

        banner.add_widget(baner_label)

        self.add_widget(banner)

    def atualizar_rec(self, *args):
        self.rec.pos = self.pos
        self.rec.size = self.size 

GUI = Builder.load_file('main.kv')

class MainApp(App):
    
    def build(self):
        return GUI
    
    def on_start(self):
        icones = os.listdir('icones')
        for foto_icones in icones:
            imagem = foto_icones
            label = foto_icones.replace('.png', '')
          
            banner = BannerSistema(imagem=imagem, label=label)
            pagina_icones = self.root.ids['sistemapage']
            lista_icones = pagina_icones.ids['scroolview_sistema']
            lista_icones.add_widget(banner) 

    def buscar_sistema(self, *args):
        pagina_sistema = self.root.ids['sistemapage']
        imagem_sistema = pagina_sistema.ids['sistema_selecionado']
        texto_png = imagem_sistema.text
        if texto_png == '':
            pagina_selecionar = self.root.ids['selecionarpage']
            imagem_selecionar = pagina_selecionar.ids['imagem_selecionar']
            imagem_selecionar.source = f'icones2/images.png'
            pagina_sistema = self.root.ids['sistemapage']
            label_sistema = pagina_sistema.ids['sistema_selecionado']
            label_sistema.text= 'SELECIONE UM SISTEMA!!!'
            pagina_selecionar.ids['label_sistema_selecionado'].text= 'SELECIONE UM SISTEMA!!!'
            
        else:

            texto_png = texto_png + '.png'
            #icones = os.listdir('icones')
            pagina_selecionar = self.root.ids['selecionarpage']
            imagem_selecionar = pagina_selecionar.ids['imagem_selecionar']
            imagem_selecionar.source = f'icones/{texto_png}'
        
            arquivos = os.listdir('arquivos')
            pagina_sistema = self.root.ids['sistemapage']
            label_sistema = pagina_sistema.ids['sistema_selecionado']
            imagem = label_sistema.text
            imagem = imagem + '.xlsm'
            for arquivo in arquivos:
                if arquivo == imagem:
                    df_arquivo = pd.read_excel(f'arquivos/{arquivo}')
                    lista_codigos = df_arquivo['CÓDIGO'].astype(str)
                    pagina_selecionar = self.root.ids['selecionarpage']
                    lista_cod_selecionar = pagina_selecionar.ids['scroolview_selecionar']
                    for item in list(lista_cod_selecionar.children):
                        lista_cod_selecionar.remove_widget(item)
                    for item in lista_codigos:
                        codigo = item  
                        banner = BannerSelecionar(codigo=codigo)
                        lista_cod_selecionar.add_widget(banner)
        time.sleep(1)
        texto_input = pagina_selecionar.ids['codigo_input']
        if imagem == 'EIMS NUM.xlsm' or imagem == 'TMS NUM.xlsm':  
            texto_input.hint_text = 'Digite o Código numérico e Click no Botão Verde ao Lado'
        else:
            texto_input.hint_text = 'Digite o Código alfabético e Click no Botão Verde ao Lado'
    def preencher_codigo(self, codigo, *args):
        
        pagina_selecionar = self.root.ids['selecionarpage']
        label_codigo = pagina_selecionar.ids['codigo_escolhido']
        label_codigo.text = codigo

    def selecionar_input(self, text):
        pagina_selecionar = self.root.ids['selecionarpage']
        label_codigo = pagina_selecionar.ids['codigo_escolhido']
        label_codigo.text = 'Código'
        label_componente = pagina_selecionar.ids['componente']
        label_componente.text = 'Componente'
        label_descricao = pagina_selecionar.ids['descricao']
        label_descricao.text = 'Descrição da Falha'

        pagina_selecionar = self.root.ids['selecionarpage']
        if text:
            texto = text
            label_codigo = pagina_selecionar.ids['codigo_escolhido']
            label_codigo.text = texto  
        else:
            pagina_selecionar = self.root.ids['selecionarpage']
            label_componente = pagina_selecionar.ids['componente']
            label_descricao = pagina_selecionar.ids['descricao']
            label_componente.text = f'[color=#FF0000]Código Inválido[/color]'
            label_descricao.text = f'[color=#FF0000]Digite um Código Válido[/color]'

    def buscar_dados(self, *args):
        codigo = ''
        pagina_selecionar = self.root.ids['selecionarpage']
        pagina_sistema = self.root.ids['sistemapage']
        label_sistema = pagina_sistema.ids['sistema_selecionado']
        
        sistema = label_sistema.text
        sistema = sistema + '.xlsm'
        label_codigo = pagina_selecionar.ids['codigo_escolhido']
        label_descricao = pagina_selecionar.ids['descricao']
        codigo = label_codigo.text
        df_arquivo = pd.read_excel(f'arquivos/{sistema}')
        label_componente = pagina_selecionar.ids['componente']
        label_descricao = pagina_selecionar.ids['descricao']
        try:
            if codigo != '' or codigo != 'Código':
                if sistema == 'EIMS NUM.xlsm' or sistema == 'TMS NUM.xlsm':
                    df_arquivo['CÓDIGO'].astype(int)
                    codigo = int(codigo)
                    if codigo in df_arquivo['CÓDIGO'].values:
                        descricao_falha = df_arquivo.loc[df_arquivo['CÓDIGO'] == codigo, 'DESCRIÇÃO'].values[0]
                        componente_falha = df_arquivo.loc[df_arquivo['CÓDIGO'] == codigo, 'COMPONENTE'].values[0]
                        label_componente.text = f'[color=#000000]Componente:[/color] [b]{componente_falha}[/b]'
                        label_descricao.text = f'[color=#000000]Descrição:[/color] [b]{descricao_falha}[/b]'
                    else:
                        descricao_falha = df_arquivo.loc[df_arquivo['CÓDIGO'] == codigo, 'DESCRIÇÃO'].values[0]
                        componente_falha = df_arquivo.loc[df_arquivo['CÓDIGO'] == codigo, 'COMPONENTE'].values[0]
                        label_componente.text = f'[color=#000000]Código Inválido[/color]'
                        label_descricao.text = f'[color=#000000]Código não Contemplado no Sistema[/color]'
                else:
                    descricao_falha = df_arquivo.loc[df_arquivo['CÓDIGO'] == codigo, 'DESCRIÇÃO'].values[0]
                    componente_falha = df_arquivo.loc[df_arquivo['CÓDIGO'] == codigo, 'COMPONENTE'].values[0]
                    label_componente.text = f'[color=#000000]Componente:[/color] [b]{componente_falha}[/b]'
                    label_descricao.text = f'[color=#000000]Descrição:[/color] [b]{descricao_falha}[/b]'
            else:
                label_componente.text = ''
                label_descricao.text = f'[color=#000000]Selecione ou Digite um Código[/color]'
        except:
            pass

    def mudar_tela(self, id_tela):
        gerenciador_telas = self.root.ids['screen_manager']
        gerenciador_telas.current = id_tela
        
    def selecionar_sistema(self, imagem, *args):
        pagina_selecionar = self.root.ids['selecionarpage']
        label_codigo = pagina_selecionar.ids['codigo_escolhido']
        label_codigo.text = 'Código'
        label_componente = pagina_selecionar.ids['componente']
        label_componente.text = 'Componente'
        label_descricao = pagina_selecionar.ids['descricao']
        label_descricao.text = 'Descrição da Falha'

        imagem_selecionada = imagem
        pagina_sistema = self.root.ids['sistemapage']
        label_sistema = pagina_sistema.ids['sistema_selecionado']
        label_sistema.text = imagem_selecionada.replace('.png', '')

        pagina_selecionar = self.root.ids['selecionarpage']
        label_selecionar = pagina_selecionar.ids['label_sistema_selecionado']
        label_selecionar.text = imagem_selecionada.replace('.png', '')
    def fechar_aplicativo(self):
        exit()
    

MainApp().run()
        