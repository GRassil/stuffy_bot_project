from openpyxl import Workbook

def make_excel(list):
    wb = Workbook()
    ws1 = wb.active
    ws1.title ='ОГЭ'
    ws2 = wb.create_sheet('Профиль')
    ws3 = wb.create_sheet('База')

    for ws in wb.sheetnames:
        wb[ws].append(["Имя", "Фамилия", "Процент решённых задач", "Всего правильно решённых задач", "Всего решено задач", "Всего решено вариантов", "Средний бал", "Максимальный бал"])

    for i in list:
        data = i[1:3] + i[5:]
        data.insert(2, (i[5]/i[6])*100 if i[6] != 0 else 0)
        data[6] = data[6] / data[5] if data[5] != 0 else 0
        if i[3] == 'ОГЭ' and i[4] >0:
            ws1.append(data)
        elif i[3] == 'ЕГЭ профиль' and i[4] >0:
            ws2.append(data)
        elif i[3] == 'ЕГЭ база' and i[4] >0:
            ws3.append(data)
    wb.save('statistic.xlsx')