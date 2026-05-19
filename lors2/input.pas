program Test5;
var
  a, b, c: integer;
begin
  a := 1;
  b := 2;
  c := 10;
  repeat
    a := a * 2;
    b := (a + b) * 2;
  until a > c;
end.