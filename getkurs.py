import os #для работы с файловой системой
import datetime
import pymysql.cursors
import argparse

stoplist = ['Привет Всем', 'Добрый вечер', 'Добрый Вечер', 'добрый вечер', "Добрый вечер!", '"', "'", 'я хочу', 'Я хочу', 'да хочу', 'Я ХОЧУ', 'Очень хочу']
entrylist = ['Агрессивное', "агрессивное", "Агрессивная", "агрессивная", "консервативная", "Консервативная", "Консервативное", "консервативное"]
chat = [] #массив чата для выгрузки
localID = 1 #локальный (в системе в отчете) идентификатор сообщения
startRowsNum = 0 #счетчик для подсчета общего кол-ва сообщений

try:
    #****************************************************
    #парсим командную строку для получения id загружаемого отчета
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--report_id')
    args = parser.parse_args()
    report_id = args.report_id

    #подключаемся к БД и выгружаем стоп-слова
    connection = pymysql.connect(host='/', user='/', password='/', database='/', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    cursor.execute("SELECT `value` FROM `stoplist`")
    stoplistDB = cursor.fetchall()
    #****************************************************

    listdir = os.listdir() #содержимое директории в виде массива
    for e in listdir:
        if(e!='getkurs.py' and e[0]!='~'): fileReport = e
    #Открываем файл csv
    handle = open(fileReport, 'r', encoding="utf8")

    def oneWord(mess):
        if " " in mess: return True
        else: return False

    def checkStop(mess):
        if type(mess)==int or mess==None or type(mess)==float or type(mess)==datetime.datetime: return False #отметаем пустые коменты и коменты-числа
        if ' ' not in mess: return False #отметаем коменты из одного слова (коменты без пробела)

        for e in entrylist:
            if e in mess: return False

        for e in stoplist:
            if e==mess: return False

        return True

    for row in handle:
            #Обрабатываем текущю строчку и сразу конвертируем данные
            if startRowsNum!=0:
                row = row.replace('&quot;', '"')
                tempRow = row.split(';')
                if len(tempRow)==12:
                    id = int(tempRow[0])#id сообщения в отчете
                    time = tempRow[1].replace('"', '')
                    mess = tempRow[2]
                    group = int(tempRow[3])#группа, 1 - юзер, 3 - модератор
                    userID = int(tempRow[4])
                    name = tempRow[5].replace('"', '')
                    isAnswer = int(tempRow[7])
                    #Счетчик для отсекания "лишних сообщений" (ответы, которые не были отвечены за 5 минут)
                    isUpload = True
                    
                    #**********
                    if checkStop(mess)==False and group!=3: 
                        startRowsNum+=1
                        continue
                    time = int(datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S").timestamp())
                    userType = 'moderator' if group==3 else 'user'
                    messType = 'false'
                    answeredMessID = 'false'
                    mess = mess.replace('"', '')
                    mess = mess.replace("'", '')
                    mess = mess.replace("`", '')
                    mess = mess.replace("\\", '')
                    mess = (mess[:296] + '...') if len(mess) > 296 else mess
                    if isAnswer==1:
                        answeredUserName = ''
                        #Ниже ищем пользователя, которому ответили. У нас есть его имя в ответе модератора
                        #Чтоб его полкчить - перезаписываем символы до тех пор, пока не наткнемся на точку или запятую
                        for sym in mess:
                            if sym!='.' and sym!=',': answeredUserName+=sym
                            else: break
                        #ниже пытаемся найти сообщение, на которое отвечает можератор. Это этого мы перебираем 
                        #каждое предыдущее сообщение и сравниваем сначала время 
                        #(у модератора есть 5 минут, чтобы ответит, иначе ответ не будет засчитан и не запишется)
                        for i in range(localID-2, 0, -1):
                            loc = time - chat[i][1]
                            if loc < 300 and i>0:
                                #ДАлее мы сравниваем имя пользователя, который писал сообщение с именем в сообщении-ответе
                                if answeredUserName in chat[i][2]:
                                    #Если имена совпадают - первое попавшееся сообщение (удовлетворяющее условия)
                                    #помечается как вопрос, а сообщение-ответ, соответственно, как ответ
                                    #Здесь же записываются id сообщений для дальнейго сопоставления в ЛК
                                    chat[i][5] = 'question'
                                    if chat[i][6]=='false': chat[i][6] = localID
                                    else: chat[i][6] = str(chat[i][6])+':'+str(localID)
                                    messType = 'answer'
                                    answeredMessID = chat[i][0]
                                    break
                            else:
                                isUpload = False
                                break
                    if isUpload != False: 
                        currArr = [localID, time, name, userType, mess, messType, answeredMessID]
                        chat.append(currArr)
                        localID+=1
                        #print(currArr)
            startRowsNum+=1
    handle.close()

    for e in chat:
        if e[3]=='moderator': print(e)

    moderators = ''
    for i in range(len(chat)-1):
        #if e[5]!='false': print(e)
        if chat[i][3]=='moderator':
            if ' поддержка //' in chat[i][2]:
                chat[i][2] = chat[i][2].replace(' поддержка //', '')
                if chat[i][2] not in moderators: 
                    if len(moderators)==0: moderators = chat[i][2]
                    else: moderators = moderators+':'+chat[i][2]
            if ' (Поддержка //)' in chat[i][2]:
                chat[i][2] = chat[i][2].replace(' (Поддержка //)', '')
                if chat[i][2] not in moderators: 
                    if len(moderators)==0: moderators = chat[i][2]
                    else: moderators = moderators+':'+chat[i][2]
            if ' (поддержка //)' in chat[i][2]:
                chat[i][2] = chat[i][2].replace(' (поддержка //)', '')
                if chat[i][2] not in moderators: 
                    if len(moderators)==0: moderators = chat[i][2]
                    else: moderators = moderators+':'+chat[i][2]
            if ' (Поддержка //)' in chat[i][2]:
                chat[i][2] = chat[i][2].replace(' (Поддержка //)', '')
                if chat[i][2] not in moderators: 
                    if len(moderators)==0: moderators = chat[i][2]
                    else: moderators = moderators+':'+chat[i][2]
        chat[i][4] = chat[i][4].replace('\\', '')
        if type(chat[i][6])==int: chat[i][6] = str(chat[i][6])

    #заносим данные в БД:
    for e in chat:
        val = '('+str(e[0])+", "+str(e[1])+", '"+str(e[2])+"', '"+str(e[3])+"', '"+str(e[4])+"', '"+str(e[5])+"', '"+str(e[6])+"', 'false', "+str(report_id)+")"
        cursor.execute("INSERT INTO `comments` (`id_local`, `time`, `userName`, `userType`, `mess`, `mess_type`, `id_answer`, `mess_condition`, `report_id`) VALUES "+val)
    cursor.execute("UPDATE `reports` SET `report_condition`='loaded', `moderators`='"+moderators+"', `mess_num`="+str(len(chat))+"  WHERE `id`="+str(report_id))
    connection.commit()

except Exception as e:
    print(e)
    exit()


#print('Изначально строк: '+str(startRowsNum))
#print('Отобрано: '+str(len(chat)))

print('success')