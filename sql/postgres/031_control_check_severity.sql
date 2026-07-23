alter table control_check
add column if not exists severity text not null default 'info';