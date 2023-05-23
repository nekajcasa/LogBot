from __future__ import print_function
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date

import secret


class DB():
    def __init__(self, credentials):
        scope = ['https://www.googleapis.com/auth/spreadsheets',
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials, scope)
        self.service = build('sheets', 'v4', credentials=creds)
        self.drive = build('drive', 'v3', credentials=creds)

    def create(self, title):
        """Naredi se nova preglednica z naslovom _title.

        """
        try:
            # oblika preglednice
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }

            spreadsheet = self.service.spreadsheets().create(body=spreadsheet).execute()

            spreadsheet_Id = spreadsheet.get('spreadsheetId')
            spreadsheet_URL = spreadsheet.get('spreadsheetUrl')
            
            mail_list_ID = secret.mail_list_ID()
            bot_mail = self.get_values(mail_list_ID, "B2")['values'][0][0]

            self.add_premission(spreadsheet_Id, bot_mail, role="writer")

            print(f"Spreadsheet ID: {spreadsheet_Id}")
            print(f"Spreadsheet Url: {spreadsheet_URL}")
            #print(f"Spreadsheet Properties: {(spreadsheet.get('properties'))}")
            return spreadsheet_Id, spreadsheet_URL
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def add_premission(self, gsheet_id, mail, role="reader"):
        """Doda se dovoljenje za pogled preglednice"""
        #writer, commenter, reader
        domain_permission = {
            'type': 'user',
            'role': role,
            'emailAddress': mail
        }

        req = self.drive.permissions().create(fileId=gsheet_id, body=domain_permission, fields="id")
        req.execute()

    def update_values(self, spreadsheet_id, range_name, value_input_option, values):
        """spreminjanje vrednosti"""
        try:
            body = {
                'values': values
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption=value_input_option, body=body).execute()
            print(f"{result.get('updatedCells')} cells updated.")
            return result
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def get_values(self, spreadsheet_id, range_name):
        """pridobivanje podatkov iz tabele"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()
            rows = result.get('values', [])
            print(f"{len(rows)} rows retrieved")
            return result
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def append_values(self, spreadsheet_id, range_name, value_input_option,
                      values):

        try:
            body = {
                'values': values
            }
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption=value_input_option, body=body).execute()
            print(f"{(result.get('updates').get('updatedCells'))} cells appended.")
            return result

        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def mrge_cells(self, Spreadsheet_ID, Sc, Ec, Sr, Er):
        """Združevanje zelic od Sc-StartColumn, Ec-Endcoum,Sr-StartRow,Er-EndRow"""
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=Spreadsheet_ID).execute()

        sheet_id = None
        for _sheet in spreadsheet['sheets']:
            if _sheet['properties']['title'] == "Sheet1":
                sheet_id = _sheet['properties']['sheetId']

        top_header_format = [
            {'mergeCells': {
                'mergeType': 'MERGE_ROWS',
                'range': {
                    'endColumnIndex': Ec,
                    'endRowIndex': Er,
                    'sheetId': sheet_id,
                    'startColumnIndex': Sc,
                    'startRowIndex': Sr}
                }
                }
            ]

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=Spreadsheet_ID,
            body={'requests': top_header_format}
        ).execute()
        
        
    def format_cell_time(self, Spreadsheet_ID, Sc, Ec, Sr, Er,form="[hh]:mm"):
        """Združevanje zelic od Sc-StartColumn, Ec-Endcoum,Sr-StartRow,Er-EndRow"""
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=Spreadsheet_ID).execute()

        sheet_id = None
        for _sheet in spreadsheet['sheets']:
            if _sheet['properties']['title'] == "Sheet1":
                sheet_id = _sheet['properties']['sheetId']

        
        top_header_format =[
                {"repeatCell": {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': Sr,
                        'endRowIndex': Er,
                        'startColumnIndex': Sc,
                        'endColumnIndex': Ec,
                        },
                    "cell":{
                        "userEnteredFormat":{
                            "numberFormat":{
                                "type": "DATE_TIME",
                                "pattern": form
                                }
                            }
                        },
                    "fields": "userEnteredFormat"
                    }
                    }
                ]

        self.service.spreadsheets().batchUpdate(
            spreadsheetId=Spreadsheet_ID,
            body={'requests': top_header_format}
        ).execute()
        
    def format_sheet(self,Spreadsheet_ID):
        # Urejanje tebele
        self.update_values(Spreadsheet_ID, "A1", "USER_ENTERED",
                         [['Vsi obiski']])
        self.mrge_cells(Spreadsheet_ID, 0, 5, 0, 1)
        self.update_values(Spreadsheet_ID, "F1", "USER_ENTERED",
                         [['Uporaba prostora']])
        self.mrge_cells(Spreadsheet_ID, 5, 9, 0, 1)
        self.update_values(Spreadsheet_ID, "A2:K2", "USER_ENTERED",
                         [['Dan','Kdo', 'do', 'do', 'Čas',
                           'Dan', 'do', 'do', 'Čas',
                           'Dan', 'Čas']])
        self.update_values(Spreadsheet_ID, "J1", "USER_ENTERED",
                         [['Skupaj:']])
        self.update_values(Spreadsheet_ID, "K1", "USER_ENTERED",
                         [['=sum(K3:K100)']])
        #formatiranje da bo pravilen zapis
        self.format_cell_time(Spreadsheet_ID,  5, 6, 2, 1000,form="dd.mm.yyyy")
        self.format_cell_time(Spreadsheet_ID,  6, 9, 2, 1000) 
        self.format_cell_time(Spreadsheet_ID,  9, 10, 2, 1000,form="dd.mm.yyyy")
        self.format_cell_time(Spreadsheet_ID,  10, 11, 2, 1000)
        self.format_cell_time(Spreadsheet_ID,  11, 12, 0, 1)
    

if __name__ == '__main__':
# =============================================================================
#     db = DB("gs_credentials.json")
#     Main_ID = secret.Main_sheet_ID()
#     datum = date(2023, 4, 2)
# 
#     if datum.day == 1:
#         print("pošiljanje stare tabele")
#         zadnji_ID = db.get_values(Main_ID, "B1:B1000")["values"][-1][0]
# 
#         for mail in secret.mail_list():
#             print(f"Mail poslan na {mail}.")
#             db.add_premission(zadnji_ID, mail)
# 
#         print("nov mesec")
# 
#         #date_new_month = str(datum.year)+"-"+str(datum.month)
#         #id_new_month, link_new_month = db.create(date_new_month)
# 
#         #db.append_values(Main_ID,"A1:A1000", "USER_ENTERED",[[date_new_month, id_new_month,link_new_month]])
# 
#         # Samo za testiranje
#         id_new_month = secret.test_sheet_ID()
#         # Urejanje tebele
#         db.update_values(id_new_month, "A1", "USER_ENTERED",
#                          [['Vsa uporaba']])
# 
#         db.update_values(id_new_month, "E1", "USER_ENTERED",
#                          [['Po dnevih']])
# 
#         db.update_values(id_new_month, "A2:F2", "USER_ENTERED",
#                          [['Dan', 'do', 'do', 'Čas', 'Dan', 'Čas']])
#         db.mrge_cells(id_new_month, 0, 4, 0, 1)
#         db.mrge_cells(id_new_month, 4, 6, 0, 1)
# 
#     zadnji_ID = db.get_values(Main_ID, "B1:B1000")["values"][-1][0]
#     datum = str(datum)
#     prihod = "8:00"
#     odhod = "10:00"
#     cas = "2:00"
# 
#     zadnja_vrstica_A = len(db.get_values(zadnji_ID, "A1:A1000")["values"])
#     db.update_values(zadnji_ID, f"A{zadnja_vrstica_A+1}:D{zadnja_vrstica_A+1}", "USER_ENTERED", [[datum, prihod, odhod, cas]])
# 
#     zadnja_vrstica_E = len(db.get_values(zadnji_ID, "E1:E1000")["values"])
#     db.append_values(zadnji_ID, f"E{zadnja_vrstica_E+1}:F{zadnja_vrstica_E+1}", "USER_ENTERED", [[datum, cas]])    
#     
# =============================================================================
    db = DB("gs_credentials.json")
    ID=secret.mail_list_ID()
    print(db.get_values(ID, "B3:B1000")['values'])