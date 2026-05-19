program Example;
var
    counter, result, limit: integer;
begin
    counter := 0;
    result := 0;
    limit := 10;
    repeat
        counter := counter + 1;
        result := result + counter
    until counter >= limit
end.