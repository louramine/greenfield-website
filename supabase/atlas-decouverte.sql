-- Greenfield Atlas, section publique « découverte » (sans jeton).
-- Renvoie uniquement les terrains au statut Disponible, en version découverte :
-- forme approximative, surface arrondie, prix en fourchette.
-- Pas de TF, pas de propriétaire, pas de sourceur, pas de lien Google Maps, pas de référence réelle (identifiant ATL-xxxxxx).
-- Relançable. Ne modifie aucune table.

create or replace function public.atlas_decouverte() returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  res jsonb;
begin
  with base as (
    select t.ref,
           coalesce(nullif(t.quartier, ''), t.localisation) as quartier,
           t.urba,
           public.carte_num(t.superficie::text) as s,
           public.carte_num(t.prix::text) as pm,
           coalesce(public.carte_num(t.forfait::text), public.carte_num(t.prix::text) * public.carte_num(t.superficie::text)) as pf,
           case when exists (select 1 from unnest(public.tf_cles(t.tf)) as k0(cle) join public.terrain_contours c0 on c0.cle = k0.cle)
                then public.tf_cles(t.tf) else array[t.ref] end as cles,
           public.gm_coords(t.google_map) as gm
      from public.terrains t
     where coalesce(t.statut, '') = 'Disponible'
  ), geo as (
    select b.*,
           (select jsonb_agg(r) from public.terrain_contours c, jsonb_array_elements(c.geom_approx) r where c.cle = any(b.cles)) as ga,
           (select avg(c.lat_approx) from public.terrain_contours c where c.cle = any(b.cles)) as alat,
           (select avg(c.lng_approx) from public.terrain_contours c where c.cle = any(b.cles)) as alng
      from base b
  ), pos as (
    select g.*,
           ((abs(hashtext(g.ref)) % 1000) / 1000.0 - 0.5) * 0.007 as dlat,
           ((abs(hashtext(concat(g.ref, 'x'))) % 1000) / 1000.0 - 0.5) * 0.008 as dlng
      from geo g
     where g.ga is not null or g.gm is not null
  )
  select coalesce(jsonb_agg(jsonb_strip_nulls(jsonb_build_object(
      'id', concat('ATL-', substr(md5(p.ref), 1, 6)),
      'q', p.quartier,
      'z', p.urba,
      's', public.carte_arrondi_surface(p.s),
      'pmlo', case when p.pm > 0 then floor(p.pm * 0.9 / (case when p.pm < 2000 then 100 when p.pm < 5000 then 250 else 1000 end)) * (case when p.pm < 2000 then 100 when p.pm < 5000 then 250 else 1000 end) end,
      'pmhi', case when p.pm > 0 then ceil(p.pm * 1.1 / (case when p.pm < 2000 then 100 when p.pm < 5000 then 250 else 1000 end)) * (case when p.pm < 2000 then 100 when p.pm < 5000 then 250 else 1000 end) end,
      'pflo', case when p.pf > 0 then floor(p.pf / 1e6 * 0.9 / (case when p.pf < 2e7 then 1 when p.pf < 1e8 then 5 else 10 end)) * (case when p.pf < 2e7 then 1 when p.pf < 1e8 then 5 else 10 end) end,
      'pfhi', case when p.pf > 0 then ceil(p.pf / 1e6 * 1.1 / (case when p.pf < 2e7 then 1 when p.pf < 1e8 then 5 else 10 end)) * (case when p.pf < 2e7 then 1 when p.pf < 1e8 then 5 else 10 end) end,
      'g', p.ga,
      'lat', round(coalesce(p.alat, p.gm[1] + p.dlat)::numeric, 4),
      'lng', round(coalesce(p.alng, p.gm[2] + p.dlng)::numeric, 4),
      'pt', (p.ga is null)
    ))), '[]'::jsonb)
  into res
  from pos p;

  return res;
end;
$$;

grant execute on function public.atlas_decouverte() to anon, authenticated;
