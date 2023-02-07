from requests import Session
import json
from pprint import pprint

class holdingApi:
    ABC = "abcdefghijklmnopqrstuvwxyz"
    ASP = [None, 20, 5, 10, 15, 10, 20, 20]
    DAYS = {"PO":"Pondělí", "ÚT":"Úterý", "ST":"Středa", "ČT":"Čtvrtek", "PA":"Pátek"}

    def __init__(self, name : int, password : int):
        self.name = name
        self.password = password

        payload = {
                'form_user_id': self.name,
                'form_password': self.password
                  }
        
        self.ses = Session()
        res = self.ses.post("https://pardubice.czholding.cz/heslo.asp", data=payload)
        res.encoding = res.apparent_encoding
        self.connect = not 'Chybné přihlášení' in res.text

    def get_balance(self):
        res = self.ses.post("https://pardubice.czholding.cz/odkaz.asp")
        res.encoding = res.apparent_encoding
        sorce = res.text
        return float(sorce.split("Zůstatek&nbsp; vašeho účtu<br> &nbsp; ")[1].split(",-</CENTER>")[0].replace(",","."))

    def get_order(self):
        res = self.ses.post(f"https://pardubice.czholding.cz/objeda.php?mkod={self.name}")
        res.encoding = res.apparent_encoding
        sorce = res.text

        data = {}

        text = sorce[sorce.index("</head>"):]

        lunches_names = []

        for idx, day in enumerate(text.split('<td width="35%" bgcolor="#FFFF00"><b><font color="#0000CC">')[1:]):
            date = day[:day.index('</font></b></td>')]
            data[date] = {}
            # print(day)
            data[date]["day"] = day[day.index('<p align="center"><b><font color="#0000CC"></font>') + 50 : day.index(' </b></td>')].replace(" ", "")
            data[date]["idx"] = self.ABC[idx]
            data[date]["lunches"] = []

            for idxl, lunch in enumerate(day.split('<h5><font face="MS Sans Serif" color="#FF0000">')[1:]):
                ldata = {}

                lunches_names.append(lunch[: lunch.index('</font></h5>')])
                ldata["name"] = lunch[: lunch.index('</font></h5>')]
                ldata["idx"] = idxl + 1
                ldata["price"] = float(lunch[lunch.index('<h4 align="center">') + 19 : lunch.index('</h4>') - 2])
                ldata["attachment"] = []

                for idxp, attachment in enumerate(lunch.split('Příloha')[1:]):
                    pdata = {}

                    id = attachment[attachment.index('name="') + 6 :]
                    pdata["id"] = id[: id.index('"')]
                    value = attachment[attachment.index('value="') + 7 :]
                    pdata["value"] = value[: value.index('"')]
                    pdata["name"] = value[value.index('>') + 1 : value.index('</font></td>')]
                    pdata["idx"] = idxp + 1
                    # print(attachment)
                    pdata["price"] = float(attachment[attachment.index('<p align="right"><font face="Arial" color="#000080" size="2">') + 61 : attachment.index('<td width="257" height="1"></td>') - 17].replace(" ",""))

                    ldata["attachment"].append(pdata)


                data[date]["lunches"].append(ldata)

        return data

    def preview(self):
        res = self.ses.post(f"https://pardubice.czholding.cz/nahled.asp?mkod={self.name}")
        res.encoding = res.apparent_encoding
        sorce = res.text

        data = {}

        text = sorce[sorce.index("</head>"):]
        if not "Cena" in text: return None
        text = text[text.index("Cena"):]
        raw_data = [i.split('size="2">') for i in text.split("<tr>")[1:-1]]
        for i in raw_data:
            day = i[2][:i[2].index("</td>")]
            name = i[5][:i[5].index("</td>")]
            data[day] = {
                "day":self.DAYS[i[1][:i[1].index("</td>")]],
                "idx":i[4][:i[4].index("</td>")],
                "lunche":name,
                "attachment":i[8][:i[8].index("</td>")],
                "abstandard":i[9][:i[9].index("</td>")]
            }
        return data

    def _get_raw_order(self, order:dict):
        order_data = self.get_order()
        data = {}

        for day in order_data.items():
            for lunche in day[1]["lunches"]:
                if lunche["attachment"] == []:
                    continue
                data[lunche["attachment"][0]["id"]] = lunche["attachment"][0]["value"]

        for day in order.keys():
            day_idx = order_data[day]["idx"] + str(order[day]["idx"] + 1)
            data[day_idx] = f"{self.name}:{day}:{order[day]['idx']}:OBĚD"

            if "attachment" in order[day].keys():
                attachment = order_data[day]["lunches"][order[day]["idx"] - 1]["attachment"][order[day]["attachment"] - 1]
                data[attachment["id"]] = attachment["value"]

            if "abstandard" in order[day].keys():
                for abs in order[day]["abstandard"]:
                    data[f"n{order_data[day]['idx']}{abs}"] = f"{self.name}:{day}:{abs + 2}:{self.ASP[abs]}:2101{abs}"
        
        return data

    def order(self, order:dict):
        
        data = self._get_raw_order(order)

        self.ses.post("https://pardubice.czholding.cz/objed.php", data=data, headers={"Accept-Charset":"cp1250"})

    def raw_order(self, order:dict):
        self.ses.post("https://pardubice.czholding.cz/objed.php", data=order, headers={"Accept-Charset":"cp1250"})

if __name__ == "__main__":
    from pprint import pprint
    api = holdingApi(2704, 926)

    order = {"08.02.2023": {"idx":12, "attachment":2, "abstandard":[4]}
    }


    # pprint(api.raw_order(order))
    # pprint(api.get_order())
    pprint(api.preview())
    # pprint(api.get_balance())