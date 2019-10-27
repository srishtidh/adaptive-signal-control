demand=1100V

for set in 001 002
do
  for case in 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018 019 020
  do
    for count in 1 5
    do
      python report_sample_statistics.py --turns ~/adasco/experiments/clean/isolated/config/isolated.turn.pkl --samples ~/adasco/experiments/clean/isolated/config/${demand}/${demand}-${case}-samples-${set}.pkl --count ${count} >> ${demand}-${case}-S${count}-R${set}
    done
  done
done
