import streamlit as st
from bs4 import BeautifulSoup
import numpy as np
from time import sleep
from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
from urllib.parse import urlparse, parse_qsl
from PIL import Image


st.set_page_config(layout="wide")


app_mode = st.sidebar.selectbox('Select Page',['Home','Help'])


if app_mode=="Home":

    st.sidebar.title("CDC Raport")

    urls_csv = st.sidebar.file_uploader('Wgraj plik ze Swiva')
    dynacrems_csv = st.sidebar.file_uploader('Wgraj plik z Dynacrems')
    chromedriver_path = st.sidebar.text_input("Podaj ścieżkę do Chromedrivera")

    def cdc_scraping(pages, chromedriver_path = chromedriver_path):

        fdata = []
        i = 1
        st.subheader("Progress bar")
        my_bar = st.progress(0)
        for page in pages:
            
            print("Start: "+str(i)+"/"+str(len(pages)))
            page_url = page + "?testMess=no&gdprForce=consent&noext=1"
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            driver = webdriver.Chrome(chromedriver_path,
                                        options = options)
            driver.get(page_url)  
            sleep(randint(5,10))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            my_table = soup.select('a[href*="dynacrems_cdc"]')
        
            data=[]
            for tag in my_table:
                data.append(tag.get('href'))
                
            fdata.append({"url": page, "date": np.unique(data).tolist()})
            print("End: "+str(i)+"/"+str(len(pages)))
            my_bar.progress((i/len(pages)))
            i = i + 1
        
        data= pd.DataFrame(fdata)
        redirects = []
        
        for i in range(0,data.shape[0]):
            box_data = []
            for j in range (0, len(data.date[i])):
                o = urlparse(data.date[i][j],  allow_fragments=True)
                box_data.append(dict(parse_qsl(dict(parse_qsl(o.query))["par"])))
            redirects.append({"url": data.url[i], "data": box_data})


        return redirects


    def generate_report(scraping_data, creations):

        df = pd.DataFrame(scraping_data)
        df = df.set_index("url")
        df = pd.DataFrame(df.apply(lambda x: pd.Series(x['data']),axis=1).stack().reset_index(level=1, drop=True))
        
        df = pd.DataFrame(df[0].values.tolist(), index=df.index)
        df = df[['creationID','pPrice','pSalePrice','pID',"pName","pCategory","shopID","shopName"]]
        df = df.set_index(['shopID','shopName', 'creationID'], append = True)
        df = df.groupby(['url','shopID','shopName','creationID']).agg(lambda x: list(x))
        
        df['position'] = df.groupby(['url','shopID','shopName']).cumcount()

        creations = creations[['creation id', 'creation name', 'template id', 'template name', 'created date', 'clicks', 'views']]
        
        data = df.reset_index()
        data['creationID'] = pd.to_numeric(data['creationID'])
        
        test = data.reset_index().set_index("creationID").join(creations.set_index('creation id'), how = 'left')
        test['ctr'] = test['clicks'] / test['views']
        return test



    st.header("Generowanie raportu")   
    if st.button("Wygeneruj raport"):
        swiv_data = pd.read_csv(urls_csv, sep = ';')
        pages = list("https://" + swiv_data["Strona Url"])

        with st.spinner("Trwa web scraping"):
            scraping_data = cdc_scraping(pages, chromedriver_path)
        st.success("Web Scraping zakończony")
            
        with st.spinner("Trwa tworzenie raportu"):
            creations = pd.read_csv(dynacrems_csv)
            report_data = generate_report(scraping_data, creations)
        st.success("Raport wygenerowany")
        st.download_button("Pobierz raport", report_data.to_csv(), file_name="raport.csv", mime="text/csv")
        st.dataframe(report_data)


elif app_mode == 'Help':
    st.sidebar.title("Instrukcja")
    st.markdown("""
    ## Opis raportu
    Raport rozszerzający dostępne wymiary w raporcie kreacji pochodzącym z Dynacrems. Kreacje są pogrupowane wewnątrz konkretnych artykułów, których one dotyczą, wzbogacone są o informacje o pozycji kreacji w artykule, produktach znajdujących się w niej oraz sklepie, którego dotyczy boks. Przykładowe wiersze z raportu:
    """)
    st.dataframe(pd.read_csv(r"C:\Users\kszymczak\Downloads\example_cdc.csv"))
    st.markdown("""
    ## Wymagane pliki
    - pobrany plik csv z wynikami kreacji z Dynacrems: https://dynacrems.grupawp.pl/panel/dashboard/
    """)
    st.image(Image.open(r"C:\Users\kszymczak\Downloads\cdc_1.png"))
    st.markdown("""
    - plik z URLami artykułów CDC: https://u.grupawp.pl/tx1a
    - Należy nałożyć dodatkowe filtry:
        - `Kontent Data Dodania` (najłatwiej wygenerować listę dat w Excelu i wkleić jako listę)
        - `Kontent Autor Mapowany` (można dodać filtr na autora artykułu, jeśli wiemy, kto pisał w danym miesiącu)
    ## Wykonanie raportu
    Niezbędne jest pobranie Chromedrivera (https://chromedriver.chromium.org/).

    Należy wgrać pliki:
    - URLe ze Swiva w formacie identycznym jak w podanym linku:
    """)
    st.dataframe(pd.read_csv(r"C:\Users\kszymczak\Downloads\example_urls.csv",  sep = ';'))
    st.markdown("""
    - dane z Dynacrems (pobrany plik CSV nie wymaga żadnych zmian)
    Należy podać ścieżkę do pliku `chromedriver.exe` w formacie:
    
    `C:\\Users\\kszymczak\\Downloads\\chromedriver.exe` **(z podwójnymi slashami)**
   
    Po naciśnięciu przycisku `Wygeneruj raport` program wykona web scraping i przetworzy dane, po czym możliwe będzie pobranie raportu za pomocą przycisku `Pobierz raport`.
    """)