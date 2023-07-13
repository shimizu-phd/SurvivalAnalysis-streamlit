import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
from lifelines import KaplanMeierFitter
from lifelines.statistics import pairwise_logrank_test


st.title('生存解析')

name = st.selectbox('検定方法を選択してください', ['ログランク検定', 'ウィルコクソン検定'])
st.write('実験の後期に差が大きいものはログランク検定、実験の初期に差が大きい場合はウィルコクソン検定が適しています.')

df = None
test = {
    'ログランク検定': None,
    'ウィルコクソン検定': 'wilcoxon'
}
df = None

way = st.selectbox('方法を選択してください.', ('直接入力', 'CSVから読み取り'))
st.write('\n')
st.write('\n')

if way == '直接入力':
    st.markdown('''
            - 下記のように検体ごとのグループ名、イベント時間、イベントをカンマ区切りで入れてください。
            - 検体の個数に制限はありません.  
            - グループの数に制限はありません.
            - グループごとの検体数は違っていても問題ありません.  
            - 多重比較検定が可能です.
            '''
                )
    st.markdown('---')
    st.markdown('''
                グループ名  
                対照, 対照, 対照, 対照, 処置A, 処置A, 処置A, 処置A, 処置A, 処置B, 処置B, 処置B, 処置B  
                イベント発生時間  
                10, 14, 14, 14, 5, 7, 10, 11, 13, 3, 5, 5, 7   
                イベント（0は生存または追跡不能、1は死亡）  
                1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1
                  
                この例では対照の1匹目は10日目に死亡、対照の2匹目から4匹目は14日間生存、処置Aの1匹目は5日後から脱走などの死亡以外の理由での追跡不能を意味します。 
                ''')
    st.markdown('---')
    group = st.text_input('各検体のグループを順に入力してください')
    time = st.text_input('各検体のイベント発生時間を順に入れてください')
    event = st.text_input('各検体のイベントを順に入力してください')

    if group and time and event:
        # 改行で分けてリストにする
        group_split = group.split(',')
        time_split = time.split(',')
        event_split = event.split(',')
        # 改行などが入っていて中身のないデータになっているものを除く
        group_split = [s.strip() for s in group_split if s.strip() != '']
        time_split = [float(s.strip()) for s in time_split if s.strip() != '']
        event_split = [float(s.strip()) for s in event_split if s.strip() != '']
        try:
            df = pd.DataFrame({
                'group': group_split,
                'time': time_split,
                'event': event_split
            })
        except ValueError:
            st.write(f':red[エラー：各データは同じ長さ・数である必要があります.]')


if way == 'CSVから読み取り':
    st.markdown('''
            - CSVファイルは一行目にグループ名、イベント時間、イベントと記載し、その下に数値を入れてください.  
            - 検体の数に制限はありません.  
            - グループの数に制限はありません.
            - グループごとのデータ数が違っていても問題ありません.  
            - 多重比較検定が可能です。
            '''
                )
    st.markdown('---')
    st.markdown('''
                |グループ名|イベント時間|イベント|
                | ---- | ---- | ---- |
                |コントロール|10|1|
                |コントロール|14|0|
                |コントロール|14|0|
                |コントロール|14|0|
                |処置A|5|0|
                |処置A|7|1|
                |処置A|10|1|
                |処置A|11|1|
                |処置A|13|1|
                |処置B|3|1|
                |処置B|5|1|
                |処置B|5|1|
                |処置B|7|1|

                この例ではコントロールの1匹目は10日目で死亡、2匹目から4匹目は14日まで生存、処置Aの1匹目は5日目以降追跡不能（脱走など）を意味します。
                ''')

    with open('./sample.csv') as f:
        st.download_button('サンプルCSVのダウンロード', f, 'sample.csv', "text/csv")
    st.markdown('---')
    st.write('')

    uploaded_file = st.file_uploader("CSVファイルをアップロードしてください.", type="csv")
    if uploaded_file is not None:
        # DataFrameへの読み込み
        df = pd.read_csv(uploaded_file)
        df = df.dropna()

if df is not None:
    st.dataframe(df)

    st.write('このデータで間違いなければ解析に進んでください.')
    st.write('入力に不足や誤りがある検体は削除されます.')

    interval = st.checkbox('グラフに信頼区間を表示する.')
    censoring = st.checkbox('グラフに検閲マークを表示する.')
    button = st.button('解析')
    if button:
        kmf = KaplanMeierFitter()

        groups = df.iloc[:, 0].unique()
        fig, axes = plt.subplots()
        for group in groups:
            group_data = df[df.iloc[:, 0] == group]
            kmf.fit(group_data.iloc[:, 1], group_data.iloc[:, 2], label=group)
            kmf.plot_survival_function(ax=axes, show_censors=censoring, ci_show=interval)

        st.pyplot(fig)

        results = pairwise_logrank_test(df.iloc[:, 1], df.iloc[:, 0], df.iloc[:, 2], weightings=test[name])
        st.dataframe(results.summary)