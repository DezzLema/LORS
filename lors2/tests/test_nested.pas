//Тест с вложенными операциями
var counter, limit, step: integer;
begin
    counter := 0;
    limit := 10;
    step := 2;
    repeat
        inc(counter);
        step := step + 1
    until counter >= limit;
    counter := step
end.