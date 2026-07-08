#!/usr/bin/env bash
# 300 oldest VNIC Logging-Analytics entities (last activity 2022-01-11..2022-12-14).
# 3+ years untouched on an ephemeral type = high-confidence dead. Reappearance auto-recreates any still-live one. Review, then run.
OCI=/Users/rishabh/bin/oci; NS=axfo51x8x2ap

# EBS-EM1  (updated 2022-01-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria6ex6jhmyh73iuosckvaat6plli374hi2asnvug4h4gda --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaa4tleua2og5sfg7p  (updated 2022-01-20) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaaxemttcmrhvc6le5ycajepbx5nhrerzatgpaswj4puoa --force --profile EMDEMO
# oke-cehbzhfelsq-ndglr2iuxiq-sgwqotetkla-2  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriautm42id7b4icycyztbnhtslcmlvcd7utwnhrmyvbawga --force --profile EMDEMO
# oke-cehbzhfelsq-n5nyr7yxiwq-sgwqotetkla-1  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaaiwn72rtarme6m5fg3xdsvugzero3owqe7pzilsy4trq --force --profile EMDEMO
# oke-cehbzhfelsq-n5nyr7yxiwq-sgwqotetkla-0  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaq3lv4bdrv6jzvxtcybzet6fzufeckcmrfe5wy34xsheq --force --profile EMDEMO
# oke-cehbzhfelsq-n5nyr7yxiwq-sgwqotetkla-2  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriazyl3zq2yingey6regz7nhpdxnplevtfs4aypddb7qmrq --force --profile EMDEMO
# oke-cehbzhfelsq-nyu7nvvpwva-sgwqotetkla-1  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2lu66hewzst3q2x3vxqoe45ept2kcdtln5e5bcb2kppa --force --profile EMDEMO
# oke-cehbzhfelsq-nyu7nvvpwva-sgwqotetkla-0  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria5lbcrj6jm2fuxyumzcqaru7otdrwtushetnicnh6t6zq --force --profile EMDEMO
# oke-cehbzhfelsq-nyu7nvvpwva-sgwqotetkla-2  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriarvbyrxy4nfwxds5h7mo5p5raxiszehl5r7g6f4w5yeba --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaaafjoyhloomxhlmg  (updated 2022-01-20) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabtm6y6abthp2vh2vbzvxkz6eiqq25hs4exrk5pl3pysq --force --profile EMDEMO
# oke-c22gcjtoueq-npyfoqultba-sakfrk54sja-2  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria3gp2qxm5n6lxplgzgpql33evtkpl4qskbvhcnrxp4yfq --force --profile EMDEMO
# oke-c22gcjtoueq-npyfoqultba-sakfrk54sja-0  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriadsaudwjb66gvhqu4fnf2uhikkqg4w75cvx5qleczawdq --force --profile EMDEMO
# oke-c22gcjtoueq-npyfoqultba-sakfrk54sja-4  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krialgrdgg4zwgckgxpid2nnqsl7fzqsxk5xd2az6am767zq --force --profile EMDEMO
# oke-c22gcjtoueq-npyfoqultba-sakfrk54sja-3  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriauhhz37i7n2hncriu4lxpvpsk5az7hegd4d2ivwpskcua --force --profile EMDEMO
# oke-c22gcjtoueq-npyfoqultba-sakfrk54sja-5  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriawzsckxptcggegxex5li2riu6wv2e7m5jxfli4jl4bkxq --force --profile EMDEMO
# oke-c22gcjtoueq-npyfoqultba-sakfrk54sja-1  (updated 2022-01-20)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriazknir6wwbv6tha2fjklybkixsmdjtd7bmb6k5ekr27uq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaa6sj3sf5gzdgs2lj4yzg5e6d  (updated 2022-01-21) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriamhbslrtd6m3dsfp4s7acd3zhokjyfx5emh44o3eapp4a --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaayhmux6m7jdrvrn5ekk23id7  (updated 2022-01-21) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaprsmvfttc7h3wx7c2uupievk72fsgpibnjonn2zpylna --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaa6sj3sf5gzdgs2lj4yzg5e6d  (updated 2022-01-21) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaekgiisibhynobkbspifjxb2zycvmeyx4yy7e4fb6wwka --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaayhmux6m7jdrvrn5ekk23id7  (updated 2022-01-21) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriazvnmu63zba6mtx723klvu6fxxxsr6dqizwchh2btdbja --force --profile EMDEMO
# oke-cx5vuifyvga-n6e5ux3t7cq-swbmc3wtebq-1  (updated 2022-01-21)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriacngwlclionj2v4nfkh45h63vbuxobvnuamdegy6dwjqa --force --profile EMDEMO
# oke-cx5vuifyvga-n6e5ux3t7cq-swbmc3wtebq-0  (updated 2022-01-21)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaxubqupzazg47vwscwhrwcooqqsgpqpnmjjrzgqxiqala --force --profile EMDEMO
# oke-cx5vuifyvga-n6e5ux3t7cq-swbmc3wtebq-2  (updated 2022-01-21)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabtu36iz3u5nzdnpm4utwmfhrv6emjar5ldllzogpm2aq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaaz3c2eqfhfbhganf  (updated 2022-01-21) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriar7jqubxwvlgbl45mmvuddobo6si6occpvybf6dutg3hq --force --profile EMDEMO
# mushopVMForATP  (updated 2022-01-21)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaswr77pkrov4rmvej3yeimekfyn3o2xplys7lzvhu4foa --force --profile EMDEMO
# test  (updated 2022-01-25)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krianw6upiiwt43sl6wbyduzunvpecuhsanaopdies376gfa --force --profile EMDEMO
# mgmt-node-mushop  (updated 2022-01-25)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria7vnalz5kmajoslbfqnpebfgaqzkei7ou27fazittv5sq --force --profile EMDEMO
# management-node-mushop  (updated 2022-01-25)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria575orbi4ao3miy5gai6nemgf6lzsm5dkm6op5el5qghq --force --profile EMDEMO
# management-node-mushop  (updated 2022-01-25)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria22he37wk7x2mua3mehe6wa5tc7mnrsdhqphl5jlolfga --force --profile EMDEMO
# management-node-mushop1  (updated 2022-01-26)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriahddceth673phe74r5imnl6eyofa6bnx2mftpemymq2iq --force --profile EMDEMO
# primaryvnic  (updated 2022-01-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaidhbxomi57z5depo2qyuils5wcgefa44rpliefotmy2a --force --profile EMDEMO
# instance-20220130-0944  (updated 2022-01-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaquyzspqltay7x44jkv2i4wj2iw4jsm6cokclwnqnhzua --force --profile EMDEMO
# primaryvnic  (updated 2022-01-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriai2bb6ic542dd5ayk3dellzl4xh3ygndsu457qvf35ziq --force --profile EMDEMO
# primaryvnic  (updated 2022-01-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabwou3oex2oe6v2s24jdeirqs472bxgpsd7nytljg5vda --force --profile EMDEMO
# primaryvnic  (updated 2022-01-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriamqy6grpch5pf3znlt2pybouctzdlcj6edn5dpragczvq --force --profile EMDEMO
# primaryvnic  (updated 2022-01-31)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatxl3xeit2o2m32qhrejh6iglviqswm6owoncgeq5moka --force --profile EMDEMO
# primaryvnic  (updated 2022-01-31)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavf7etffgj37pvlcg5335vzxa3saudju2zmmcb7wbm5tq --force --profile EMDEMO
# logan-worker-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria4byd3qdcdnpmar3atjulewvv4io7au47nrbwlm3m4m7a --force --profile EMDEMO
# logan-master-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria7ud3kpap3swli5jhkdkhk65zb5xrewvzrzu7lvcwil3q --force --profile EMDEMO
# logan-master-002  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabsa6xviklnuitczxlfoocwog4knv3wuyxjuydyoquvea --force --profile EMDEMO
# logan-worker-003  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriacb3pywo363uifznnfentz3azjco52wbc46efo6si2ata --force --profile EMDEMO
# logan-worker-002  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaec6fjdvbm5jjs5h7bcvlekmfhdndbqyh2ogo27mhk6bq --force --profile EMDEMO
# logan-api-server-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriahl4m3djf4x5gtusck7q3cfyhwg6ajstbj7rbnctux7ua --force --profile EMDEMO
# logan-master-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaasmscmr2n3xnrgywt3tp56pmyo6vxznwro64hmgmch6q --force --profile EMDEMO
# logan-worker-003  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriahslowbvtjnwigzmdxazjmyn5byxon7rfes6yy5ondhsq --force --profile EMDEMO
# logan-master-002  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriam7uyg4pjmzlsnacuokr2nprothdgv2ustc5wd3wud5eq --force --profile EMDEMO
# logan-worker-002  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriantaazwri6josiismviw36hqwrpyrc6hucfw4x2l4nz4q --force --profile EMDEMO
# logan-api-server-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriapn6i4nquvaplg7c6djliwhsidaxnyxvpzqpqbjmyzhjq --force --profile EMDEMO
# logan-worker-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaw7cylmeymzhziotii4l6og7gjvz5uvdihhyiy5lyuevq --force --profile EMDEMO
# logan-master-002  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria4ap722mdnlvvmaumdyvyqteetzznyyclxf4c6rtpg6iq --force --profile EMDEMO
# logan-worker-002  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria4rrv4dalrg6nhzzlxd6wx5j3kqubuelviwofewqpxzjq --force --profile EMDEMO
# logan-worker-003  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaei5ipueuxefxiydsbzfmhbt4itmyldf7excejjdponqq --force --profile EMDEMO
# logan-api-server-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaicqvumkxcvf5d4yu2kayh5cxi6oilj7dvnf6zmk4gbja --force --profile EMDEMO
# logan-bastion-vnic  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaom33vsojew27eykbnazpd5colvg5gqkkbqlfcq7djhxq --force --profile EMDEMO
# logan-worker-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriauakr2s6zifnwtgfk32pk2tcbhx5boerazsnzm6ff2fea --force --profile EMDEMO
# logan-master-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaumypahfghtkwbbpdgvmiqhrcsxat5rvrwmkp74xct63q --force --profile EMDEMO
# logan-master-002  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria3bz3xtlfa75sks2j334dnjx7gfnlfyvcck6g4bkmrlaq --force --profile EMDEMO
# logan-master-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria6fv24no7eetx53xd2sduqb45zpmd5bjwwge5hxi7qwaa --force --profile EMDEMO
# logan-worker-002  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriacxywofl2j5jvhqilxef2ocgkgcvamkkpzhuhyd7zirlq --force --profile EMDEMO
# logan-worker-003  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriadd7aowjuqejnmqhvvndvddqjji5vexowkf3qinthyuaq --force --profile EMDEMO
# logan-api-server-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krianm4ww4d6zhlykgzalnnbe2ishv5ekpllmuwa2sydndga --force --profile EMDEMO
# logan-worker-001  (updated 2022-02-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavqfpnvjdtm554yr7aexf4cyx7iqxxsg7cry5hhgehscq --force --profile EMDEMO
# logan-master-002  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria762arldnkiwj3svwktaipbtsy4s5r5pt5g6x3fdyxfqq --force --profile EMDEMO
# logan-worker-002  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabi32oddtopl56ypamcreumnajqqotruwatih2dcwnxla --force --profile EMDEMO
# logan-worker-003  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriajx4dmh5q5gdpysyeldxak4ouws3ejqnjtipvlwgzelha --force --profile EMDEMO
# logan-api-server-001  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriataewvrkw5eavfavddh34irmipvlwueido65yyoaqx6da --force --profile EMDEMO
# logan-master-001  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriathcfb2c5ljwqzzxu43i6mssaazuvxbweyt2tofnb5kua --force --profile EMDEMO
# logan-worker-001  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriadhejkrimgkbfjlax2mylmyapgqixayshlhvmxg3uo2tq --force --profile EMDEMO
# logan-master-001  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaa354yncrsn2nmfxyvqehjf5sufj62wchacieoubybawa --force --profile EMDEMO
# logan-api-server-001  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriab6r35pqi7ktuxqzubfjbwzcuw5zxgecjcse2bvrww2gq --force --profile EMDEMO
# logan-master-002  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriakdscz53ldna3e36wtuewy673ivkld6wdqlxiwwppzlwa --force --profile EMDEMO
# logan-worker-002  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaoyup2zd6ersynqchf6jhsaz7k4dgq6jyl2bpogozbshq --force --profile EMDEMO
# logan-worker-003  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriasmtytafyrmrlu7vexjkmmjsk2rucdwo33mf5l2egxu3a --force --profile EMDEMO
# logan-worker-001  (updated 2022-02-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatrswwdco5uyt7j3dwqxyrpzw4mbhn3fxje5wqky6p2rq --force --profile EMDEMO
# logan-worker-001  (updated 2022-02-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabhgpuoxwgkvnusg75all2zdaimb6tu53aylipzasvvea --force --profile EMDEMO
# logan-api-server-001  (updated 2022-02-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaan4ajd4ypn7gnic45sd4exnt27qxdqp2yo43gxuro6uq --force --profile EMDEMO
# logan-worker-002  (updated 2022-02-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabdhlwrko6y4waxbn4ohfrgi2o653fhrdd4t2c54fag2q --force --profile EMDEMO
# logan-master-002  (updated 2022-02-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriapd6csqpo6byins7unduqtif5khdo7oqqegvnmn3rtiga --force --profile EMDEMO
# logan-master-001  (updated 2022-02-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriastjzdzvglvtmhfyw7l5e6t4gy2cycdmfc3i2k25l4sba --force --profile EMDEMO
# logan-worker-003  (updated 2022-02-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriacb5jzowsg3vt5fkuivqb6vk6tgw42gf6l7fnbnol6kya --force --profile EMDEMO
# emcc-hol-s01-2022-02-17-013530  (updated 2022-02-17)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatohhifqjgkila2nkxf7mbhsmkxvfvb2m2qafhlb22zfa --force --profile EMDEMO
# vnic20220222080514  (updated 2022-02-22)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavkro2z7xg6bc24obwte7vzu4ojazfnbogdlcq7f3oqga --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaretr7tojwsraglfbbzesjqz  (updated 2022-02-22) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krialj7gbgln5gpq5co3tazvxltge66bniweek3yswbisxrq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaz5nzdchpgzjr3y4dd4jequ7  (updated 2022-02-22) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaoor2qrgzubo5hag4gj7r56nnu2n5m47lveaeuri6fxcq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaz5nzdchpgzjr3y4dd4jequ7  (updated 2022-02-22) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriax4fir7qucdi72c2xg2olhsrtkosn322ye7w3dfofclxq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaretr7tojwsraglfbbzesjqz  (updated 2022-02-22) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriab7gzht2nek5texb3aha4kexgc3tajfppqv5rzksghhgq --force --profile EMDEMO
# ocid1.bastion.oc1.phx.amaaaaaaqgp2kriaayk7uegzkeixeulmwy5scpf67kwtuweh  (updated 2022-02-22) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria662b26fjzju6e4fftjdpa7z2ctyymeguxbe2enxvup6a --force --profile EMDEMO
# LA-MySQL  (updated 2022-02-23)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriagqat2xfreoem45h54f2wgx7wvdtw462bpcqm5gn6aipq --force --profile EMDEMO
# vnic20220223060340  (updated 2022-02-23)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krianhh35mw23hjgnaxqv74wctpjydkures6j3um5okkd3hq --force --profile EMDEMO
# EBS_LA_2502  (updated 2022-02-25)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaevrhxlypxjhosszzol2oorzcuqk3kswnff5mm6kvldbq --force --profile EMDEMO
# MySQL-LA  (updated 2022-02-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriajejn6rwi2avkxcwav3yygcajsqephsodgy4zcchwtdvq --force --profile EMDEMO
# EBS-CMgr  (updated 2022-02-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krialczttpbesqviozqkkt7mnop6wxxdpjhuamcesqqmswbq --force --profile EMDEMO
# OraDB_LA  (updated 2022-03-07)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriahvj4m3rohylqauoplqy2caejea4cej73ix367q44xqmq --force --profile EMDEMO
# fss-1000000033278745  (updated 2022-03-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriate3sewrrai4wie46juntt5khrnan4waor4redsgsu3zq --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-03-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaynld3wc6zn2rxpy5rglzrurvquyfugnhh3vacha5nita --force --profile EMDEMO
# mySQL-instance  (updated 2022-03-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriap53cfy2ea2mmvr7rmiov3q2dx5fmrt6q7ek3ayoaqg2q --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-03-14)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2t2zftgmukaawppoi6s2ld65dlqo6g37l3ix64jbv4ba --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaxarlxnaok7ybce7oiifun6r  (updated 2022-03-18) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriagvjiqshbj2z4h2v2r74d53max3k4mzysw6wn4rzahbda --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaxarlxnaok7ybce7oiifun6r  (updated 2022-03-18) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatdr4u4y42pjenwxfr7p3vffsmnpdc62e4atehmvjs6ja --force --profile EMDEMO
# vnic20220330060343  (updated 2022-03-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavetrkiywj3zdxtwpsk6r4mbuwivff7rcwgp2n2mxcsnq --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-04-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaf4o4c7wh5yjcoczzkiy35td7czalgssrh7b4wzxset4q --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaaeoqfltndxzyuxvx  (updated 2022-04-12) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriamu7b7iylr7twbo4cnqkoomdnta5szwhuapgibb5v57ca --force --profile EMDEMO
# oke-cvr5eqcvzaq-nadym5tplpa-sbqkkzseeka-2  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria7timyylojvfdlckqjqcmp6hqrqcmdhuyrltd5tvjc75a --force --profile EMDEMO
# oke-cvr5eqcvzaq-nadym5tplpa-sbqkkzseeka-0  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriajwrpizgqujsfwgd534ycopaxfqvj2qilvfuibm2nwkxq --force --profile EMDEMO
# oke-cvr5eqcvzaq-nadym5tplpa-sbqkkzseeka-1  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaroyx75ydv5ti6yhavb7o3zc7g6vgtodjelbf4r7gdmpq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaa43u6jt6hsf5dmvy  (updated 2022-04-12) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria3w4wfs4az6thy4xft2infcw4dski734df6ewc6q263ea --force --profile EMDEMO
# oke-clvgvt3qsna-ndobgl7f7uq-snl3ku4wdnq-1  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriam67agpyhnjct25miffgf5x3azogz4tujrtpveqbqrmdq --force --profile EMDEMO
# oke-clvgvt3qsna-ndobgl7f7uq-snl3ku4wdnq-2  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriarukn4o4fkpkan7a4q4o4xkfgaju6q2bqxtmhpbj5tcpq --force --profile EMDEMO
# oke-clvgvt3qsna-ndobgl7f7uq-snl3ku4wdnq-0  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavaxhsi2hqhc5klogeldvxivamhxumzxtug7lpldeoxiq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaaonww2eqt5j5xz5n  (updated 2022-04-12) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaexxg53p2hbhpfmd5ybtm72rrjky4hxzodsffthljpdoq --force --profile EMDEMO
# oke-cleohaxjjtq-nj5lqrcaflq-so7bc5m2gxa-3  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria5fpg7kdunq66cwfqtxfl2hlgkeq4srk4ftu3bevasc3a --force --profile EMDEMO
# oke-cleohaxjjtq-nj5lqrcaflq-so7bc5m2gxa-2  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriagtkhmp7rhzhfgz5lf7xdr5sfehfov47yyfzxaeyjrwoa --force --profile EMDEMO
# oke-cleohaxjjtq-nj5lqrcaflq-so7bc5m2gxa-1  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriakpklv2aja6wbtfnrlpucccz3bzohc3cktksj2o4c4kma --force --profile EMDEMO
# oke-cleohaxjjtq-nj5lqrcaflq-so7bc5m2gxa-0  (updated 2022-04-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriayzydvztwteldcsnqrfgnkn7kzdwbx6fvyoy6pkxnr6bq --force --profile EMDEMO
# gitlab-subnet  (updated 2022-04-21)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriag3sauhefsqddfqtmds22nreibga6y2akhut4dj2yqj4a --force --profile EMDEMO
# cluster5-bastion  (updated 2022-04-22)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria6nykzxycsokb5osntbrw3edhmzkyah6yt67hxpfwtusa --force --profile EMDEMO
# cluster5-bastion  (updated 2022-04-22)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriakmrqx2k557sn2o5bneuul4hrruqobkx76utnyqxtmgyq --force --profile EMDEMO
# vnic20220504060404  (updated 2022-05-04)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krialerybyc52g7dgutpqpteehuwk7wikeym3mntk5ijttma --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-05-16)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriapnw5lx2r6igy3nto3z4xfoelq3jtbyyptcql7f7qzeqa --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-05-16)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaaxngo2xvqwh6t4z3pyw2thqksdclzyishimqtllhq6ja --force --profile EMDEMO
# vnic20220525060336  (updated 2022-05-25)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriay2mvfoql6o5lv4yzlxgo7mvgm7xfkjkpz62dx2uy2bba --force --profile EMDEMO
# vnic20220530020137  (updated 2022-05-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria5z5gflb2lxun7lzgm7w5rukpkviwvodd5qw32nizmtga --force --profile EMDEMO
# vnic20220530225446  (updated 2022-05-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria3egicathl5fv2jbfp6eu356c4225otopu4jxpmgpp3jq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaa5akz5ddjrjxqhlfxajoqoqy  (updated 2022-06-03) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2iy5o64cjbmzz33lffx674c6zrcftzatjr2346etdhna --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaa5akz5ddjrjxqhlfxajoqoqy  (updated 2022-06-03) [parent GONE]
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaeag22wigjt6qkdwng7m2x6ikaeney6ssh63o4vzdg36a --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-06-03)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriawwu6z5wumkcjn43gbfqppkwmmax66href6u43gzcoieq --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-06-15)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabxcup5mw4fqmctppj7qn5nwd3he3hwi7bmpg2d66zvda --force --profile EMDEMO
# vnic20220622060358  (updated 2022-06-22)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria4nvmecfc7zpdsj3pghdv7utet2ltt4i7siiponz3jmhq --force --profile EMDEMO
# siebel  (updated 2022-06-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaoaejcsahyac3aqoamiyq2sdp4ru4ad5sd4ceat4t7blq --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-07-19)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriafmlhgvw4ugn3ijh5fwzpsdynqszw42gxepumo4c2s4tq --force --profile EMDEMO
# vnic20220727060350  (updated 2022-07-27)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatiiqzondotkllg5b4lvj2o5rk6cb7i4ksavx2zurl2cq --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-07-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaqudfmt4wppoifoksdqnigd32ziev5pcxanticrb2zuwq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaadg6y3ifhe33meqz  (updated 2022-08-01)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriagpnlakf7p6bn7uolz6hg2tzc46ntqtentmgmixjhsgka --force --profile EMDEMO
# oke-cn23zfqx6ta-nyw5wxcrhta-so5q7w6uyza-0  (updated 2022-08-01)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriasnfnrfusglf4a7kfqlk5aajpo4lfakkarsybfg3bothq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaav75jkquzw33ftne  (updated 2022-08-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria4e2mt6jikyy3gbieqrb4wtb6vbicfro67irts5iy62xa --force --profile EMDEMO
# oke-cz4w5deblja-ndekqfh2x4q-sbjil44yhtq-2  (updated 2022-08-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaixphndrxlwqku5ocf5z5ad5rdgeby4npybm545xagb7a --force --profile EMDEMO
# oke-cz4w5deblja-ndekqfh2x4q-sbjil44yhtq-5  (updated 2022-08-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriazlwfqqt5ifdipnyfmbzbpdlfvwrzeywireza63gnwg2q --force --profile EMDEMO
# oke-cz4w5deblja-nsyh52kmyna-sbjil44yhtq-2  (updated 2022-08-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriamgyi3kxetbqesfls7o2fwtp7jfodmh4t4seoa3yub6nq --force --profile EMDEMO
# oke-cz4w5deblja-nsyh52kmyna-sbjil44yhtq-5  (updated 2022-08-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krianj5kxngzsewmviigbwrgcuuxujwo2usuryp3mrqwzzeq --force --profile EMDEMO
# oke-cz4w5deblja-nsyh52kmyna-sbjil44yhtq-4  (updated 2022-08-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriav2fau6zqeog4gxjkj6zorw6av6velbuhj745z75ry5iq --force --profile EMDEMO
# oke-cz4w5deblja-nsyh52kmyna-sbjil44yhtq-1  (updated 2022-08-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriazlfrfbcq24cw7kyryakta67uoef7blkaewrzbaivoooa --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaakduwizxhuvklwp7h4jy2dp2  (updated 2022-08-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriacxvthw32ehcw7rwidmebczbggejc4aytvvba6s5bepwq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaakduwizxhuvklwp7h4jy2dp2  (updated 2022-08-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriambx27zomua4fjychpzfk4iche2fvkswv4k4pzl5ggpka --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-08-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriar2i66ru5cgb4jmngdvzklibaivw6lnyw2lkpnmcepohq --force --profile EMDEMO
# fss-3000000044157741  (updated 2022-08-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2hwkkkukno3gasbcwyw3x664mjh53zunectuzrt75uha --force --profile EMDEMO
# fss-3000000044157741  (updated 2022-08-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaiwm5k4dvr5oqof2dpixghy45pvzr3jpmddbrfsc6tgaa --force --profile EMDEMO
# vnic20220809184544  (updated 2022-08-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaq7jzwtvpvxgnywdfoofjcvh72fwclwswi5tgr2cgf2kq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaa6p3yw4wgprke2tlvmbvrcot  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria6zrcz5dritbchamtipswsjdkbu7qbvyhv6kqjkwcfxqq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaa6p3yw4wgprke2tlvmbvrcot  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaejvhhprxux7c632cbn6azjvrhscuvkhzjpbxy2oybgrq --force --profile EMDEMO
# fss-2000000044222036  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria3bqwlcz7sll7totktb56daoxh4s3tw5jl7kh3azazwca --force --profile EMDEMO
# fss-2000000044222036  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaymf5bt62eodkcqlfhsppuyzvvindspug6d3g2i74ebgq --force --profile EMDEMO
# Web-Server-1  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaxwell5hm773dzf4puzad2lujyhlqzz4rt4wthjqgcvtq --force --profile EMDEMO
# vnic20220810193635  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2yaapl4hjiohprvhabxtnftweqqmq7cf5gnxnnhvo5gq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaaskvivfpqkatfpsl  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria3qjv2zhuvitttbigd7kw4ztuttytbu2ooq7spqoidiaa --force --profile EMDEMO
# vnic20220810232631  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria6yg56znzbxs4qllp2qj622mrrtj5a7are2cb5wcma5vq --force --profile EMDEMO
# oke-cldsxftwsnq-n2r3oxfrgia-sgwqotetkla-4  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriacmkhx6474hx67ce7cgsgp3nxmqwtemk3fe3ojlgjskqa --force --profile EMDEMO
# vnic20220810232621  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriactrh5tytsn5v4tiz3gbucpc2awic23gujvof3vu5747q --force --profile EMDEMO
# oke-cldsxftwsnq-n2r3oxfrgia-sgwqotetkla-3  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaibsir5brjs2igd6fqfrwqlbde2md6fzhztk4i4dwu6qa --force --profile EMDEMO
# oke-cldsxftwsnq-n2r3oxfrgia-sgwqotetkla-0  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriajz5mlcrbc74s7j3tqxtczp2zusxr7zbd64f4eh62wntq --force --profile EMDEMO
# oke-cldsxftwsnq-n2r3oxfrgia-sgwqotetkla-2  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriao63glm6mt4mdm3baosxdeunp7ek2ihi3d5mmgm5emzca --force --profile EMDEMO
# vnic20220810232631  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaphjtfcbovfun7d7koz6pht3ep2a33iih2ew6r5ob5y6q --force --profile EMDEMO
# oke-cldsxftwsnq-n2r3oxfrgia-sgwqotetkla-1  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatqtgu4gaua37qr7fvl5fgiofxc2g3hymn3j4sq3w2r2q --force --profile EMDEMO
# vnic20220810232641  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaxvsdqkq26rlavzvnmmpaxf2yfjuq2eja36c6fpugx5gq --force --profile EMDEMO
# vnic20220810232641  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriajyngxppxjfssp2kevmxaq4iy25rn7ejnzt2ro7h3m7oq --force --profile EMDEMO
# oke-cozn3lpaj6q-nitbnyoiawq-sakfrk54sja-1  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaf7b2uh7btl34u672uqy6mubd5jy6ofm6z4dnmbgrzivq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaanz2ega6yvyqtosg  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriahczapirqoeudomxkkuqlrttnjvyj2ns4j3kjizbxrt2a --force --profile EMDEMO
# oke-cozn3lpaj6q-nitbnyoiawq-sakfrk54sja-2  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriakeysgeyblz7bo3mk6xmaro2yeonf5eujeutfmtitlzla --force --profile EMDEMO
# oke-cozn3lpaj6q-nitbnyoiawq-sakfrk54sja-0  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriankbektlyk6kgg6sqa7b73mwsfjhneh6gyk7pc3kkowna --force --profile EMDEMO
# oke-cozn3lpaj6q-nitbnyoiawq-sakfrk54sja-3  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriahhvjz5qa6rys3i3d6cll3t5ntdlg3pgzvqf5w73mdh7q --force --profile EMDEMO
# oke-cozn3lpaj6q-nitbnyoiawq-sakfrk54sja-4  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krian422ragso7iu2eg4wsu5bsbfuq2gbcir74gb2ncjpb4q --force --profile EMDEMO
# vnic20220810235537  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria3uloxqiiyipfhyttocz72jyvt7pdn5ij4mlcusbjchbq --force --profile EMDEMO
# vnic20220810235537  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krianej5nbr3bdf76scb7yvwcmkfnewtpiglttop4bminilq --force --profile EMDEMO
# vnic20220810235528  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krias554lr7oo4qngleidji3iwaybxrb5jcl3hqgz7fs4t4q --force --profile EMDEMO
# vnic20220810235539  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriasqmbyqdhnu4lztem5zzq7vau54niapm5fiqnv4qpwv7q --force --profile EMDEMO
# vnic20220810235538  (updated 2022-08-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriauoswjkz2lldjjx37ar7q4sfz5mflytcdy6vh2ubxglia --force --profile EMDEMO
# vnic20220811000406  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriayicempvpz2u7mgxqjebditf6nmqhhk3wqj3gxcwdbuuq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaaq2yv2zebl5jdr3u  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaskh6giqhvdih7dlrfulczmo6fgca2xrdd47nqvbnkjea --force --profile EMDEMO
# oke-cvufubuepha-n3ytn2ibapq-sakfrk54sja-1  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaacyoe3khmo4ymzul33ym34jjhctohlyiiean6gqkkkma --force --profile EMDEMO
# oke-cvufubuepha-n3ytn2ibapq-sakfrk54sja-0  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriadsl33qmvq3s44ec2jwvprt5to5oohp3gzoihifufrnua --force --profile EMDEMO
# oke-cvufubuepha-n3ytn2ibapq-sakfrk54sja-2  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriazfcrh5hqwbqdhe25idi33yf6ck7vppqfd2iki2kizhya --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaym4ew7ptt6lpxs2btgvhg5u  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaj6mvtlq4i5rcvxxcy27qb5c5z42x7fa5s3tplanhwnma --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaym4ew7ptt6lpxs2btgvhg5u  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriazfsjvgehrshdar5nyfoibytlg66qlsi5wsnlmz3zakvq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaas6w2ak4hdr3nzxipwboomgv  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria72rgrqfsqf2u2l4q47ymt3owt7u2oh7o3pvufm7xausq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaas6w2ak4hdr3nzxipwboomgv  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaz2wtzlwtljbtjfsxmc32nfvhqyqo5exesieckomo4yvq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaajwckyrs3qw7mn7bnzpnw4pb  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krialyjki6bsuepxq6qltahopwnck6agh2qu4fuzvfdc4erq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaajwckyrs3qw7mn7bnzpnw4pb  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatga6bupwuh2fqoalgwpxdqd6qxy6yah3wq6j3wvkuz6q --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaltnmnls2afmx5bsac367ujb  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krialsg3os6bxl7aswtvirzit2w4claqjqsf2qotogk7txza --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaltnmnls2afmx5bsac367ujb  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriax4u7fo2ctc7q7oxzqe5khkdtvqz7etasiaqwl7c3rota --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaxhewghvrer7jtxybil2h7fb  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavvkkn2oahfhrofvvromztso4dqbzfk6djoor3bgoswtq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaxhewghvrer7jtxybil2h7fb  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaiocgabrzojuj56cylmvvfvm3kc25amy4qijjmwpcgmza --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaawgwpx5s4ypycf3td7idim33  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaj262ztfvcrvu4wrwsor5etbnmpzu44mnpnau6xxfx76q --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaawgwpx5s4ypycf3td7idim33  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriayryxydrj3kqjpn7ohmzo2xowq3sbb5gm7wey423csbwq --force --profile EMDEMO
# oke-cktejbky4zq-nr4ws4pq5ha-sakfrk54sja-1  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria4zs6oemedbehhokl5weph7vfsymvyhgpvonxqgs2k42q --force --profile EMDEMO
# oke-cktejbky4zq-nr4ws4pq5ha-sakfrk54sja-0  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaav4qffg3koavpcgzrqq6iey62tm6iewfxbekxlmedrbq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaaamwwwzoe4wwkeik  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaffhsuif7crcupwathtao732x3eqewi2lbfscpqsl5qgq --force --profile EMDEMO
# oke-cktejbky4zq-nr4ws4pq5ha-sakfrk54sja-2  (updated 2022-08-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaxbexq4dopnwha4fpog6pypyoftxhdrp3jib4idiaipgq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaa6jo5xkcdeb54yzgrfhrfvv2  (updated 2022-08-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria4xrwdzzwdnxfalvddod3qkgrpqc42jzyt2htlbob2isa --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaa6jo5xkcdeb54yzgrfhrfvv2  (updated 2022-08-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriajkazljeesmtfgmqznabckuxqsujmwjfcndsegkmjxiaq --force --profile EMDEMO
# fss-mnt-2000000044222036  (updated 2022-08-15)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriadunuzijzql47lzuqo52jfrxnojfeopsebvl22rjerh5a --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaa6ft5tbj3lvesa6fgbu722m  (updated 2022-08-15)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriap2s54tgteaj5gfvfbvlw7kdibwjtdisuil5m2chrw42q --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaa6ft5tbj3lvesa6fgbu722m  (updated 2022-08-15)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriab2nlkirj7von6ksogjhkqst7loubsygfp634mpszipoq --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaab6xuhmstzjbzhsg  (updated 2022-08-16)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaxwawkbihseyhzsxgz37u4hzkx4j76sfttu5j35nl4rjq --force --profile EMDEMO
# oke-cpdmfvtboca-noxrul7zlqa-slb2j3kfewq-2  (updated 2022-08-16)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabrgmwmmhksfrtbssdzyozndi25khrjb5qtljyzn7kvpq --force --profile EMDEMO
# oke-cpdmfvtboca-noxrul7zlqa-slb2j3kfewq-0  (updated 2022-08-16)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaskdoct6afk6t734z3lboxkntlvp23cii65wp62cbccsa --force --profile EMDEMO
# oke-cpdmfvtboca-noxrul7zlqa-slb2j3kfewq-1  (updated 2022-08-16)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaxmcn427zhklktpueizxwm7hmo7ctu3rh6rjoowvrodsa --force --profile EMDEMO
# vnic20220817060415  (updated 2022-08-17)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaj2ezdh2fqqgnwbodbk4zj34hasfihckuvktlemznq6cq --force --profile EMDEMO
# vnic20220818092756  (updated 2022-08-18)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriadcmo2yxpc5tcclu3bxik6wt7sryk22wizrii52d7ruma --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-08-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriau2l3kwa743p2rnzenqiccvh6hyxijjzf4ufdup5bhdhq --force --profile EMDEMO
# fss-mnt-2000000044222036  (updated 2022-08-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaxlgpbpsvvh2pf3wn6fmka5ceskzaj2weut4swh5qiqbq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaae6524ow3ttvbavfjuc73szw  (updated 2022-08-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriad4q2k5gukrlos2y3cn76ka7bnlzbdx7aft76abdjmrka --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaae6524ow3ttvbavfjuc73szw  (updated 2022-08-30)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriao2oclguz6gbcsvlmrxkvvz4takbmttzlsqdai5ywytia --force --profile EMDEMO
# Service VNIC for cluster ocid1.cluster.oc1.phx.aaaaaaaax7dtb2f2u2jajz6  (updated 2022-09-06)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriawwadjiefpgp4jdrzmzmnwtmkxdz23vsoopshjetnfvwa --force --profile EMDEMO
# oke-ccxy6dcu3ta-ngzbt6v63ia-sakfrk54sja-1  (updated 2022-09-06)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2bjwh2brofioqiebxh4iwqasxbpdsvcneaxz62kl5rqa --force --profile EMDEMO
# oke-ccxy6dcu3ta-ngzbt6v63ia-sakfrk54sja-2  (updated 2022-09-06)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriac4hem3ngsyubet3gdgwfox3d23y3d6vpuajgy4ct3t4q --force --profile EMDEMO
# oke-ccxy6dcu3ta-ngzbt6v63ia-sakfrk54sja-0  (updated 2022-09-06)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriayogtjncoui2o2fxrsucxu6ts3aa5gywqls3wn4jyljsa --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaaymfud763x3vbqkqrtnnls5l  (updated 2022-09-07)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriayetyqb7726surmpupe5hcz7j2tr3u35ln45lrhjhi3wa --force --profile EMDEMO
# MDS-Client-DBTest  (updated 2022-09-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2yegsfbo2tlfhiaeyhw24bec2e5vlewoiegj4phgyrha --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaamjm6ggbpsxm6hhn7gmcbi4p  (updated 2022-09-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria6ancae7cfqhysbpairm2lxdhdnqbp4r7446jywlgtira --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaan7uneiumevcfif53njjccqp  (updated 2022-09-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaa4fryz7uqu5zbfjp6a2tgjx6hyrgszc6tnljr22k5aca --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaailfed6taylivkl25rgbfc2y  (updated 2022-09-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaezspbajfpzi5me7rews54624chat4yz6kytbfmkgri6q --force --profile EMDEMO
# fss-3000000046641212  (updated 2022-09-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriac56csvznf3kyq6ypciw4etnsgskmita4vo3l24d36kga --force --profile EMDEMO
# fss-3000000046641212  (updated 2022-09-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriax4zovgy5rprzh7lj3drbynlygruoa75uosza6a5e7dea --force --profile EMDEMO
# fss-mnt-3000000046641212  (updated 2022-09-15)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriamgiafsber7dsmkxod7lg42oo6ddx5nwoizomim7q5ohq --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-09-16)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriayuzr6z4rmuh5cp3sfpm6772yfe5tzxhtvo6c3oxwgttq --force --profile EMDEMO
# VNIC for LB ocid1.loadbalancer.oc1.phx.aaaaaaaa4qyiakeegq252fimb224qv3  (updated 2022-09-19)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaph7ladnpz6c42wquuorrgz7qeeqo7tgldetlffnjyznq --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-09-19)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriakjwr3luko6z62pfmemvizb6r6sndgct5zhz7ft6qkcaq --force --profile EMDEMO
# fss-mnt-3000000046641212  (updated 2022-09-19)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriawzviq64va7ds2hoxn32j2yxyfcmq2sastf3mtmqeeora --force --profile EMDEMO
# mushop-primary-cluster  (updated 2022-09-21)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2cl2ejm3ndql4a4bxskghmvzn7zwafkfplpn74bwlqga --force --profile EMDEMO
# vnic20220922092841  (updated 2022-09-22)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriastcinym66olmzztqx2z242bhtxu3scmki4rstquzrolq --force --profile EMDEMO
# vnic20221026061013  (updated 2022-10-26)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaqqtjf4dsvfrtp6gbldzqlxhud3ruzmw3w4ycyywrdska --force --profile EMDEMO
# vnic20221027092925  (updated 2022-10-27)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabviiijyddtbghv2j36ijkio5lhh32pbi7t3uxxvsgolq --force --profile EMDEMO
# vnic20221101085332  (updated 2022-11-01)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria7ztk7j34fjqz43h64sluzlq7wadrvh6gd644j2use77q --force --profile EMDEMO
# fss-mnt-3000000046641212  (updated 2022-11-22)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2gjreith6ervqgjdmsmpz4j52vkgej52sxwzkqlgssnq --force --profile EMDEMO
# ocne-controller-01  (updated 2022-11-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabmjbtla6m7zwl6sgdyivhlpc6h7yyg7prjgdg6cyg4eq --force --profile EMDEMO
# ocne-8x8-operator  (updated 2022-11-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaxeps24uxzkhproyzobv5j5linnmzcjhccukdbwwiiktq --force --profile EMDEMO
# ocne-controller-02  (updated 2022-11-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2vq5l565bj7n4pt7mc4oh4mv6hly2sfe535eybxz2dca --force --profile EMDEMO
# ocne-8x8-worker-01  (updated 2022-11-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaekb2vvuoyfpytpaitvelkgh66v4h2vo3ocmxf2usrs2a --force --profile EMDEMO
# ocne-8x8-worker-02  (updated 2022-11-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriamqxiprtz543qe3cscjn5rumxrv3p6vxljg7bqbfjddpq --force --profile EMDEMO
# ocne-controller-03  (updated 2022-11-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriasov4bplwk6awmpehp6rzntgupbgzybmfp5degyuiekaa --force --profile EMDEMO
# ocne-8x8-worker-03  (updated 2022-11-28)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriawlw62hcppb6lycyoo6vfarjy3krbghe7sxcx2hv4sj7q --force --profile EMDEMO
# vnic20221202063305  (updated 2022-12-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriat4zc5grjqaqcxads5gvizi6kynyyb46moxlhr5riuw6q --force --profile EMDEMO
# vnic20221202113318  (updated 2022-12-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria4ke6m7tlbkfoyn3ynijjwc6gof7s7be2dwviduv7aslq --force --profile EMDEMO
# vnic20221202171153  (updated 2022-12-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2pdbqmq2lfsqvdqus5kdwj6v6dgz63oyxspsdcaiw4cq --force --profile EMDEMO
# vnic20221202225050  (updated 2022-12-02)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriag7g2io7oohdgij36cg2r26h6d73idi7sqijbqe6qqyuq --force --profile EMDEMO
# vnic20221203042140  (updated 2022-12-03)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaqpruftaqrzihhoat25ay6aq5p776szz6mowomdel4s4q --force --profile EMDEMO
# vnic20221203101942  (updated 2022-12-03)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavd4l44j2l4bgs7f2omkfx57jxdvfavpj6u4e2elvyzqa --force --profile EMDEMO
# vnic20221203151112  (updated 2022-12-03)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriay5egijiznbwubgdm4mbktae23ih3gihxhn6dxri4gz3a --force --profile EMDEMO
# vnic20221203200412  (updated 2022-12-03)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaxeoxh5icav3ccposrkzzka5bwfhjkotf6lp3ruqwnbaq --force --profile EMDEMO
# vnic20221204011113  (updated 2022-12-04)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriahee7k6e4ltaeig7viwmoyqmqea65w6mvmxitkldbicsq --force --profile EMDEMO
# vnic20221204061116  (updated 2022-12-04)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria2scjrmcuthtmrtq7v2d7tntndg5e2q3vxhvxczmuidvq --force --profile EMDEMO
# vnic20221204115050  (updated 2022-12-04)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriauoceunltuzorqz33o3c3gzbfolyghsaswllo6qwakc2q --force --profile EMDEMO
# vnic20221204172428  (updated 2022-12-04)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria7rotcjqvzbi3qqavyngmp5kwdu65jeyyn4dttqnc2ura --force --profile EMDEMO
# vnic20221204232328  (updated 2022-12-04)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria7hzerqmfdh7ae7ibvzysmvvrfhmns4r3xqsyaxkb3baq --force --profile EMDEMO
# vnic20221205044951  (updated 2022-12-05)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaunvlop5j6cvfnoyp7capn427xy6kvummlbtmqdpxj2pq --force --profile EMDEMO
# vnic20221205094741  (updated 2022-12-05)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria3inljpjrwdhe4saepbtdchfmntltnqp2yivxmjckb3vq --force --profile EMDEMO
# vnic20221205153953  (updated 2022-12-05)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriayizgheklva7yx2kgslagxfbv2n3ggryasdba2owgggka --force --profile EMDEMO
# vnic20221205210724  (updated 2022-12-05)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaab42ym6jv4apqx6crrcqmp3dq2sjk7ocq7mhtkzqfika --force --profile EMDEMO
# vnic20221206022126  (updated 2022-12-06)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaycroeq2uocbxqhy27ln2kjmcmhpgqccwhlmzhyi52pna --force --profile EMDEMO
# vnic20221206080936  (updated 2022-12-06)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavub7d5soyal64hmh23xe56xgbxlswclsyzqdfc3b5tcq --force --profile EMDEMO
# vnic20221206085247  (updated 2022-12-06)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriale2bvgq7vxrce3pc66sbj3lqsaf2pgyq66dfib75gt5q --force --profile EMDEMO
# vnic20221206135343  (updated 2022-12-06)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria6447iiavi64iibayet3tcurh5dnedksv2ww5nkxojbkq --force --profile EMDEMO
# vnic20221206194545  (updated 2022-12-06)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaogg3pw2i7fnug6r3jstsumrxhyjufjoy3eii6yfbyoeq --force --profile EMDEMO
# vnic20221207012032  (updated 2022-12-07)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaohq6zz542oklrakyp7iz7dc2afgdiawsm7cez2bhlm4a --force --profile EMDEMO
# vnic20221207060932  (updated 2022-12-07)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria26hab4oe2ar4jhtyrriiadgc5xgz2ekhbzcqwzpqefeq --force --profile EMDEMO
# vnic20221207070419  (updated 2022-12-07)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatnkjfcrnlajut2sjxnjiwhwcrvugwuur4iegb2acrjqq --force --profile EMDEMO
# vnic20221207124250  (updated 2022-12-07)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavbr7ipnwibpkjzduekndh2ycsslhpk2hegigp7t4broq --force --profile EMDEMO
# vnic20221207173358  (updated 2022-12-07)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriab4py4ar4k62gcbiynhgs36qlx2sci2iqvwcntnokdraq --force --profile EMDEMO
# vnic20221207231904  (updated 2022-12-07)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria6uogf6irlyk7p7c4n22o3wa32wxxjem5dqaca5aa6bqa --force --profile EMDEMO
# vnic20221208044215  (updated 2022-12-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriarmkegclc44vqilr4xzlad2x64pklkkyomdttbh2rcmta --force --profile EMDEMO
# vnic20221208092945  (updated 2022-12-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriafvhunvdarw65xcfptwxacnulhtrse6ja3jo2ekz5elfa --force --profile EMDEMO
# vnic20221208102228  (updated 2022-12-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria6sxiaowgb74de6b3wnsf7hsdbhyz6b5evre4ro4lvssa --force --profile EMDEMO
# vnic20221208152252  (updated 2022-12-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaqlml3lc3oouos7rozkj6sppzbxv5eplg4o4zr2sfsvaq --force --profile EMDEMO
# vnic20221208210639  (updated 2022-12-08)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriawgmkly23p4prqedxtxvph65od5bjoehlk6fw35vo4iqq --force --profile EMDEMO
# vnic20221209022059  (updated 2022-12-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatpgtgyfxyz7dtoo5r6kagrjv6qc464nhoenm7nbhelzq --force --profile EMDEMO
# vnic20221209073222  (updated 2022-12-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabuixr4g7zkxkeywve6lo4qrydmfnuqrvnf5nteud5rza --force --profile EMDEMO
# vnic20221209124014  (updated 2022-12-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaafc7vybfk6odppf5txzs4lhyk6durdiezkvbcqskmcuq --force --profile EMDEMO
# vnic20221209173035  (updated 2022-12-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriauh4m6q5nefbnphqzyodoyt4nxole33qt7crgaq4alana --force --profile EMDEMO
# vnic20221209223216  (updated 2022-12-09)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaurggwfseow4kue4xuuwxnithbbqph63fjqoqfr4f3qxq --force --profile EMDEMO
# vnic20221210033944  (updated 2022-12-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kria5hbwcnppfuczh2jlcqdb5tvq3jyrqtpwz2qmgs2pqdfa --force --profile EMDEMO
# vnic20221210084927  (updated 2022-12-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaflcaqr7cju667vvza2a354s3rzmoshpe7juu6euuhjha --force --profile EMDEMO
# vnic20221210143603  (updated 2022-12-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriapwdqgt3e5qczvacr53pkafk2vx44yzuhfrmnpp6xkpkq --force --profile EMDEMO
# vnic20221210195920  (updated 2022-12-10)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2krianspb7xzytdu343fkkkg6bhqldtleoh64velciodxghvq --force --profile EMDEMO
# vnic20221211015827  (updated 2022-12-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaon5p3mdgojbksxwzytciehbevopfhko44rng7xbhtvma --force --profile EMDEMO
# vnic20221211071753  (updated 2022-12-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriatnftzjxsxo5eurwd564il2gbktud34aqhsgwbmgl7o4a --force --profile EMDEMO
# vnic20221211123624  (updated 2022-12-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriamqu5eldkj5didacy3wiegbrynnijimwufcits62lhzma --force --profile EMDEMO
# vnic20221211175224  (updated 2022-12-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriakfmcnfpax6tvktztsfnpw3lzfoesmleghduqbizv3yvq --force --profile EMDEMO
# vnic20221211234022  (updated 2022-12-11)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriag5e3rfbju677ihpj4d4xv4p5lu4q5zgxq5gpwp5mv54a --force --profile EMDEMO
# vnic20221212051905  (updated 2022-12-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriawvfiyyf5x25knazc2q4bzdwcblejxkszhivvh76oub7q --force --profile EMDEMO
# vnic20221212105943  (updated 2022-12-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaq2ir6fwobpmgb67ebdxfabbpo2rrk45vzbgn5vshtqjq --force --profile EMDEMO
# vnic20221212155135  (updated 2022-12-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriavggfofmjqdjwhbe4lnmn3ogcat2hsprdm3phfwph2jta --force --profile EMDEMO
# vnic20221212212349  (updated 2022-12-12)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaft4g2kemxawck4k4qjwoopweakkbjnjjkksoqksu2wqq --force --profile EMDEMO
# vnic20221213032034  (updated 2022-12-13)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriabe7mxzjjqf7ptfgr6wbgakxfs6znpo26tf5b27ivrc4a --force --profile EMDEMO
# vnic20221213090847  (updated 2022-12-13)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriahg3cjeqwurvbrbxvwwj4cz2a7pu743bqlrgizipy4xia --force --profile EMDEMO
# vnic20221213140038  (updated 2022-12-13)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriarzrzmbseefxbo5kxqw2mxpiqipkg7ppywibn433fm4oa --force --profile EMDEMO
# vnic20221213185705  (updated 2022-12-13)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriayq3hpoojrfsbuywyrulfz7gzcj45j5ujobqgnpdzjwma --force --profile EMDEMO
# fss-mnt-3000000046641212  (updated 2022-12-13)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriahiclr7kontkjghbd6gohedu7zsfahnqousavp3lpoi2q --force --profile EMDEMO
# vnic20221214004335  (updated 2022-12-14)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriazu2ytqdrpeq6fonjtlhmfufmmpzbu5lmlpbp6evco4wq --force --profile EMDEMO
# fss-mnt-1000000033278745  (updated 2022-12-14)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriae5ufw7zzr5m5tdgeohgoup66k6e34fx4nxsnchoxdria --force --profile EMDEMO
# vnic20221214061619  (updated 2022-12-14)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriacobey5rxe5eruylx2ulvepkx623nmmnkfvni6ofqb6qq --force --profile EMDEMO
# vnic20221214115653  (updated 2022-12-14)
$OCI log-analytics entity delete --namespace-name $NS --entity-id ocid1.loganalyticsentity.oc1.phx.amaaaaaaqgp2kriaphgq4erzxzg5zxuufqzblrhdbla2moernr4e4ehqfiqa --force --profile EMDEMO
