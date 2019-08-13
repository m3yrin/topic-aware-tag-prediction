# Tag generation for Japanese article
Re-implementation of "Topic-Aware Neural Keyphrase Generation for Social Media Language"

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/m3yrin/topic-aware-tag-prediction/blob/master/qiita_tag_prediction.ipynb)

Auther : @m3yrin

## Reference
* Papar
Topic-Aware Neural Keyphrase Generation for Social Media Language  
Yue Wang, Jing Li, Hou Pong Chan, Irwin King, Michael R. Lyu, Shuming Shi  
https://arxiv.org/abs/1906.03889  
ACL 2019 Long paper

* https://github.com/yuewang-cuhk/TAKG
* https://github.com/m3yrin/NTM

* Qiita data gathering
    * https://qiita.com/pocket_kyoto/items/64a5ae16f02023df883e  
    "Qiitaの記事データは、機械学習のためのデータセットに向いている"

## Dataset
Qiita articles. These are mainly technical articles written in Japanese.  
https://qiita.com/

You can gather articles through Qiita API.  
https://qiita.com/api/v2/docs?locale=en

## Memo
* Some methods are not implemented
Beam search and copy mechanism are not implemented.

* GPU instance is recommended
`qiita_tag_prediction.ipynb` is tested on Google Colaboratory with GPU instance.   
If you feel training is slow, please check instance type.


