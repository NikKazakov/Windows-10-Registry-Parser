# Windows-10-Registry-Parser
registry.py:
Registry - основной класс реестра. Подгружает заголовок и hive bins.
Regf - главный заголовок файла реестра, просто набор полей
Hbins - итератор для загрузки объектов hive bin
Hbin - подгружает заголовок и ячейки в cells

cells.py - вся информация, связанная с ячейками. Полноценно реализованы KeyNode и HashLeaf
common.py - абстракции, наследуюемые разными классами:
Block - байтовый набор полей, предоставляет функцию unpack для чтения поля и lazy-load для полей (поля будут загружены только при вызове)
LazyList - итератор, реализующий lazy-loading для своих объектов. Используется для описания списка чего-либо

Пример запуска в main.py, вывод на тестовом файле:
> python .\main.py r\SYSTEM
Registry SYSTEM
reg.registry.Regf at 0x0, contains 24 fields
reg.registry.Hbins at 0x1000, loaded 0 items, 0/17375232 bytes
Total hbins: 3674
reg.registry.Hbin at 0x1000, contains 5 fields
reg.cell.KeyNode at 0x1020, ROOT
reg.cell.KeyNode at 0x1170, ActivationBroker
reg.cell.KeyNode at 0x1358, Plugins
reg.cell.KeyValue at 0x1628, (Default)
reg.cell.KeyValue at 0x16a0, TypeID
