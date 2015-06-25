set title "Histogram of fractions of items per StackScore"
set label "<- items with no usage data are given a StackScore of 1" at 3,0.7
set ylabel "Fraction of items"
set xlabel "StackScore"
#set noborder
set key right top
set tics in
#set noxtics
set grid
set xrange [0:101]
set yrange [0.0000009:1.1]
set logscale y
set boxwidth 0.4

plot "harvard_stackscore_distribution.dat" using ($2-0.25):3 title "Harvard" with boxes fs solid 0.7,\
     "cornell_stackscore_distribution.dat" using ($2+0.25):3 title "Cornell" with boxes fs solid 0.7

