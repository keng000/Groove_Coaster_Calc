# -*- coding: utf-8 -*-
from module_for_groove_calc import *

keta = 13

while True:
    while True:
        LOGIN_ID = raw_input("NESiCA: ")
        if len(LOGIN_ID) == keta:
            break
        else:
            print "IDは%d桁です"%keta
    PASS = raw_input("パスワード: ")

    flag = raw_input("OK?(y/n):")
    if flag == 'y':
        break
    else:
        print ""

print ":"

LOGIN = GROOVE_LPSOLVE(LOGIN_ID,PASS)
LOGIN.prepare_cookie()
True_or_False = LOGIN.check_cookie()

if True_or_False:
    print "ログイン成功しました"
    YN = raw_input("スコア更新しますか？(更新する場合、何か入力後enter):")

    LOGIN.update_music_id_list()
    LOGIN.prepare_dictionary()

    if YN:
        print "現在の全曲スコアを集計します....."
        LOGIN.get_score_list()
    else:
        LOGIN.import_file()

    print ":"

    LOGIN.get_total_score()

    print "現在のトータルスコアは " + "{:,d}".format(LOGIN.total_score) + "点です。"

    aim = int(raw_input("目指す点数は?: "))

    print "\n組み合わせを算出します....."

    LOGIN.solve_LP(aim)

    print "\n終"

    LOGIN.delete_cookie()
else:
    print "ログインに失敗しました,IDとパスワードとご確認ください"
