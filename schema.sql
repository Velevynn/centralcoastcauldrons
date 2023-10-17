create table
  public.cart_items (
    cart_id bigint generated by default as identity,
    item_id bigint not null,
    quantity bigint not null,
    constraint cart_items_pkey primary key (cart_id, item_id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (cart_id),
    constraint cart_items_item_id_fkey foreign key (item_id) references potions (potion_id)
  ) tablespace pg_default;

create table
  public.carts (
    cart_id bigint generated by default as identity,
    customer text not null,
    constraint Carts_pkey primary key (cart_id)
  ) tablespace pg_default;

create table
  public.global_inventory (
    id bigint generated by default as identity,
    num_red_ml integer not null,
    gold integer not null,
    num_blue_ml integer not null,
    num_green_ml integer not null,
    num_dark_ml bigint not null,
    constraint global_inventory_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.potions (
    potion_id bigint generated by default as identity,
    red_ml bigint null,
    green_ml bigint null,
    blue_ml bigint null,
    dark_ml bigint null,
    item_sku text null,
    quantity bigint null,
    name text null,
    price bigint null,
    constraint potions_pkey primary key (potion_id)
  ) tablespace pg_default;