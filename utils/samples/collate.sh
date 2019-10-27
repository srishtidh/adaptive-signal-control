for count in 1 5
do
  for set in 001 002
  do
  echo ========================================================================================
  echo S${count}-R${set}
  echo
  echo "Distances from expectation"
  cat *1100*S${count}-*R${set}* | grep Dist | cut -d ' ' -f5
  echo
  echo Variances
  cat *1100*S${count}-*R${set}* | grep Var | cut -d ' ' -f3
  echo ========================================================================================
  echo
  done
done
