SELECT p1.name AS "", p3.name AS "Ne voulait pas offrir à", p2.name AS "Et a finalement offert à"
FROM people p1
JOIN people p2 ON p1.target = p2.id
LEFT JOIN people p3 ON p1.exclude = p3.id