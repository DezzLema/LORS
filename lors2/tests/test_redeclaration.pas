// повторное объявление переменной
program Test4;
var
  x: integer;
  x: integer;
begin
  x := 1;
  repeat
    x := x + 1;
  until x = 10;
end.