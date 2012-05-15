drop table if exists tests;

create table tests (
    id integer primary key autoincrement,
    mine string not null,
    title string not null,
    started_at timestamp not null default CURRENT_TIMESTAMP,
    completed_at timestamp
);

create table data_points (
    id integer primary key autoincrement,
    requests integer not null,
    seconds integer not null,
    at timestamp not null default CURRENT_TIMESTAMP,
    test integer not null,
    FOREIGN KEY(test) REFERENCES tests(id)
);
