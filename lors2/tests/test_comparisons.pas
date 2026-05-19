//Тест с разными операторами сравнения
var i, j, k: integer;
begin
    i := 5;
    j := 10;
    k := 15;
    repeat
        i := i + 1
    until i = j;
    repeat
        j := j - 1
    until j <= k;
    repeat
        k := k - 1
    until k <> 0;
    i := j
end.