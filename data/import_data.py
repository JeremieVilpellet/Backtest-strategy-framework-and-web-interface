import datetime as dt # Importation du module datetime pour gérer les dates
import pandas as pd # Importation de pandas pour la manipulation des données
import numpy as np # Importation de numpy pour les opérations numériques
import blpapi # Importation de l'API Bloomberg
from blpapi.exception import IndexOutOfRangeException # Importation de l'exception IndexOutOfRangeException de blpapi
from dateutil.relativedelta import relativedelta


class BLP(object):
    @staticmethod
    def BDH(securities, fields, startdate, enddate, period='MONTHLY', calendar="ACTUAL", currency=None, fperiod=None, verbose=False):
        """
        Méthode pour récupérer des données historiques de Bloomberg.
        :param securities: liste ou chaîne de caractères des titres
        :param fields: liste ou chaîne de caractères des champs
        :param startdate: date de début
        :param enddate: date de fin
        :param period: périodicité (par défaut 'MONTHLY')
        :param calendar: calendrier (par défaut 'ACTUAL')
        :param currency: devise (optionnel)
        :param fperiod: période de fréquence (optionnel)
        :param verbose: booléen pour afficher des messages de débogage
        """
        startdate = BLP.convert_date_type(startdate)
        enddate = BLP.convert_date_type(enddate)
        
        blp_start_date = BLP.datetime_to_string(startdate)
        blp_end_date = BLP.datetime_to_string(enddate)
        
        if startdate > enddate:
            raise ValueError("Start date is later than end date") 
        
        session = blpapi.Session() 
        
        if not session.start():
            raise ConnectionError("Failed to start session") 
        
        try:
            if not session.openService("//blp/refdata"):
                raise ConnectionError("Failed to open //blp/refdata")
        
            refdata_service = session.getService("//blp/refdata") 
            
            request = refdata_service.createRequest("HistoricalDataRequest") 
            
            BLP.add_elements_to_request(request, "securities", securities)
            BLP.add_elements_to_request(request, "fields", fields)
            
            request.set("periodicityAdjustment", calendar)
            request.set("periodicitySelection", period)
            request.set("startDate", blp_start_date)
            request.set("endDate", blp_end_date)
            
            if currency:
                request.set("currency", currency)
            
            if fperiod:
                overrides_bdh = request.getElement("overrides")
                override1_bdh = overrides_bdh.appendElement()
                override1_bdh.setElement("fieldId", "BEST_FPERIOD_OVERRIDE")
                override1_bdh.setElement("value", fperiod)
            
            if verbose:
                print("Sending Request:", request.getElement("date").getValue())
            
            session.sendRequest(request) 
            
            results = BLP.process_response(session, fields, verbose)
        
        finally:
            session.stop() 
        
        if not isinstance(securities, list):
            results = results[securities]
        
        df = BLP.construct_dataframe(securities, fields, results) 
    
        return df

    
    @staticmethod
    def index_weights(index_name, ref_date):
        """
        Méthode pour récupérer les poids des composants d'un indice à une date de référence donnée.
        :param index_name: nom de l'indice
        :param ref_date: date de référence
        :return: liste des tickers modifiés
        """
        ref_date = BLP.convert_date_type(ref_date)
        
        session = blpapi.Session()
        
        if not session.start():
            raise ConnectionError("Failed to start session.")
        
        if not session.openService("//blp/refdata"):
            raise ConnectionError("Failed to open //blp/refdata")
        
        service = session.getService("//blp/refdata")
        request = service.createRequest("ReferenceDataRequest")
        
        request.append("securities", index_name)
        request.append("fields", "INDX_MWEIGHT_HIST")
        
        overrides = request.getElement("overrides")
        override1 = overrides.appendElement()
        override1.setElement("fieldId", "END_DATE_OVERRIDE")
        override1.setElement("value", ref_date.strftime('%Y%m%d'))
        session.sendRequest(request) 
        
        end_reached = False
        df = pd.DataFrame()
        while not end_reached:
            ev = session.nextEvent()
        
        if ev.eventType() == blpapi.Event.RESPONSE:
            for msg in ev:
                security_data = msg.getElement('securityData')
                security_data_list = [security_data.getValueAsElement(i) for i in range(security_data.numValues())]
                
        for sec in security_data_list:
            field_data = sec.getElement('fieldData')
            field_data_list = [field_data.getElement(i) for i in range(field_data.numElements())]
            
        for fld in field_data_list:
            for v in [fld.getValueAsElement(i) for i in range(fld.numValues())]:
                s = pd.Series({str(d.name()): d.getValue() for d in [v.getElement(i) for i in range(v.numElements())]})
                df = df.append(s, ignore_index=True)
            
        if not df.empty:
            df.columns = ['TICKERS', ref_date]
            end_reached = True
            tickers = df['TICKERS'].to_list()
            modified_tickers = [ticker + ' Equity' for ticker in tickers]
        return modified_tickers
    
    
    @staticmethod
    def get_historical_index_members(self, index_name, startdate, enddate):
        """
        méthode pour récupérer les tickers d'un indice entre deux dates de référence.
        :param index_name: nom de l'indice
        :param start_date: debut du range de date 
        :param end_date: fin range de date du range de date
        :return: dictionnaire avec les dates comme clés et les tickers comme valeurs
        """
        index_startdate = BLP.convert_date_type(startdate)
        index_enddate = BLP.convert_date_type(enddate)
        if startdate > enddate:
            raise ValueError("Start date is later than end date") 
        tickers_dict = {}
        while index_startdate <= index_enddate:
            tickers = BLP.index_weights(index_name, index_startdate)
            tickers_dict[index_startdate] = tickers
            index_startdate += relativedelta(years=1)
        return tickers_dict
    
    
    @staticmethod
    def convert_date_type(date):
        """
        Assure que la date est au format datetime
        :param date: str, timestamp, datetime
        :return: date au format datetime
        """
        if not isinstance(date, dt.date):
            if isinstance(date, pd.Timestamp):
                return date.date()
        elif isinstance(date, str):
            return pd.to_datetime(date).date()
        else:
            raise TypeError("Date format not supported")
        return date
    
    @staticmethod
    def datetime_to_string(date):
        """
        Convertit une date au format datetime en chaîne de caractères au format Bloomberg
        :param date: date au format datetime
        :return: chaîne de caractères au format Bloomberg
        """
        return f"{date.year}{str(date.month).zfill(2)}{str(date.day).zfill(2)}"
    
    @staticmethod
    def add_elements_to_request(request, element_name, elements):
        """
        Ajoute des éléments à une requête Bloomberg.
        :param request: requête Bloomberg
        :param element_name: nom de l'élément
        :param elements: liste ou chaîne de caractères des éléments
        """
        if isinstance(elements, list):
            for elem in elements:
                request.getElement(element_name).appendValue(elem)
        else:
            request.getElement(element_name).appendValue(elements)
            
    @staticmethod
    def process_response(session, fields, verbose):
        """
        Traite la réponse de Bloomberg.
        :param session: session Bloomberg
        :param fields: liste ou chaîne de caractères des champs
        :param verbose: booléen pour afficher des messages de débogage
        :return: résultats sous forme de dictionnaire
        """
        results = {}
        
        while True:
            ev = session.nextEvent()
        
        for msg in ev:
            if verbose:
                print(msg)
            
        if msg.messageType().__str__() == "HistoricalDataResponse":
            sec_data = msg.getElement("securityData")
            sec_name = sec_data.getElement("security").getValue()
            field_data = sec_data.getElement("fieldData")
        
        if isinstance(fields, list):
            results[sec_name] = {}
        
        for day in range(field_data.numValues()):
            fld = field_data.getValue(day)
        
        for fld_i in fields:
            if fld.hasElement(fld_i):
                results[sec_name].setdefault(fld_i, []).append([
                fld.getElement("date").getValue(),
                fld.getElement(fld_i).getValue()
                ])
        else:
            results[sec_name] = []
        for day_i in range(field_data.numValues()):
            fld = field_data.getValue(day_i)
            results[sec_name].append([
            fld.getElement("date").getValue(),
            fld.getElement(fields).getValue()
            ])
        
        if ev.eventType() == blpapi.Event.RESPONSE:
            break
        return results
    
    @staticmethod
    def construct_dataframe(securities, fields, results):
        """
        Construit un DataFrame à partir des résultats.
        :param securities: liste ou chaîne de caractères des titres
        :param fields: liste ou chaîne de caractères des champs
        :param results: résultats sous forme de dictionnaire
        :return: DataFrame
        """
        df = pd.DataFrame()
        
        if not isinstance(securities, list) and not isinstance(fields, list):
            results = np.array(results)
            df[securities] = pd.Series(index=pd.to_datetime(results[:, 0]), data=results[:, 1])
        
        elif isinstance(securities, list) and not isinstance(fields, list):
            for tick in results.keys():
                aux = np.array(results[tick])
        
            if len(aux) == 0:
                df[tick] = np.nan
            else:
                df = pd.concat([df, pd.Series(index=pd.to_datetime(aux[:, 0]), data=aux[:, 1], name=tick)],
                axis=1, join='outer', sort=True)
        
        elif not isinstance(securities, list) and isinstance(fields, list):
            for fld in results.keys():
                aux = np.array(results[fld])
                df[fld] = pd.Series(index=pd.to_datetime(aux[:, 0]), data=aux[:, 1])
        
        else:
            for tick in results.keys():
                for fld in results[tick].keys():
                    aux = np.array(results[tick][fld])
                    df_aux = pd.DataFrame(data={'FIELD': fld, 'TRADE_DATE': pd.to_datetime(aux[:, 0]), 'TICKER': tick, 'VALUE': aux[:, 1]})
                    df = df.append(df_aux)
                    
                    df['VALUE'] = df['VALUE'].astype(float, errors='ignore')
                    df = pd.pivot_table(data=df, index=['FIELD', 'TRADE_DATE'], columns='TICKER', values='VALUE')
        
        return df
