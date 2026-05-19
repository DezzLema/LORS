//Тест с необъявленной переменной
program Test3;
var
  x: integer;
begin
  x := 0;
  repeat
    x := x + 1;
    y := x * 2;
  until x = 5;
end.