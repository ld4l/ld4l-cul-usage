set title "Distributions of counts for different usage metrics at Cornell"
set ylabel "Fraction of bib ids with any usage data"
set xlabel "Count with given metric"
set key right top
set tics in
set grid
set xrange [0.9:200000]
set logscale x
set yrange [0.00000009:0.4]
set logscale y

plot "circ_dist.dat" using 1:4 title "circulation (recent)" with boxes fs solid 0.4,\
     "charge_dist.dat" using ($1*0.97):4 title "charge (old)" with impulses lw 2,\
     "browse_dist.dat" using ($1*1.03):4 title "browse" with impulses lw 2
