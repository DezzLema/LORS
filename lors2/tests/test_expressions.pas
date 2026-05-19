//Тест со сложными выражениями и сравнениями
var a, b, c, result: integer;
begin
    a := 100;
    b := 200;
    c := 300;
    result := a + b - c;
    inc(result);
    repeat
        a := a - 10;
        b := b + 5
    until a < b;
    c := result
end.