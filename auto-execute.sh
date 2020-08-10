#!/usr/bin/env bash
CUDA_VISIBLE_DEVICES=2

ori_path='images/HR/'

inter_path='images/LR/'
model_path='model/0809-1245L_model/model_epoch_2.pkl'
saved_prefix='30x30_'
format='bmp'
block_size=20
hei=2580
wid=2580
dep=40
date 
for count_d in range((dep//block_size))
do
for count_h in range((hei//block_size))
do
for count_w in range((wid//block_size))
do
python generate_subblocks.py --countd $count_d --counth $count_h --countw $count_w --interpath $inter_path --model $model_path  --format $format
done
done
done
python restore_complete_3Dimage.py --oripath $ori_path --interpath $inter_path  --memo $saved_prefix --block_size $block_size
date 
