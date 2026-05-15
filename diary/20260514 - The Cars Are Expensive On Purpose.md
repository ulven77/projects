# 20260514 — The Cars Are Expensive On Purpose

The day was spent turning a pile of vehicle data into something that finally tells the truth about what owning three cars actually costs.

## What happened

Most of the session was building out the vehicle financial reality report — a proper per-car breakdown covering operating costs, scheduled bills, and crucially, a monthly accrual toward each car's eventual replacement. The report covers all three household vehicles: the Volvo S80 (RKN218), the Toyota Avensis (PTJ029), and the Kia e-Soul (MSA52U).

The big design decision was committing to the fleet model exclusively. The report had been carrying both consumer depreciation (Avskrivning) and fleet replacement accrual (Ersättningsreserv) as separate TCO lines — which double-counted the capital cost. We stripped Avskrivning out entirely and let Ersättningsreserv carry the whole weight. Each car now accrues a fixed monthly amount toward its replacement by December 2032, when we expect to rethink the whole fleet strategy rather than replace cars one by one based on odometer.

The monthly deposits came out honest: 3,337 kr for the Volvo, 4,038 kr for the Avensis, and 5,728 kr for the Kia — the last one is pricier because it covers km-based service accrual, heavier insurance, and larger replacement target. Three burnup charts were generated showing cumulative savings from June 2026 to December 2032, one per car, each with milestone markers and a target line. The session also produced a gather script for the session:end skill — compressing what was previously a stream of individually-approved tool calls into a single batch script that collects history, git state, diary, and goals in one shot.

## Interesting moments

The moment that stuck was realising the "true-cost deposit" calculation: total annual costs divided by 12, where "total" includes not just the scheduled bills in the YAML but also the monthly recurring costs that don't appear as individual line items — fuel, replacement accrual, tire reserve, km-based service. Getting that right meant the ledger saldo values stayed identical even as the deposit number changed, because the increase was exactly absorbed by the new cost bucket being tracked.

## How it felt

_"Im happy about where the report is going, the burnups are good and I like the data I get from the report. It feels like the cars are expensive but thats why I want the report in the first place. To show the actual costs, which I now believe they do."_
~ Ulf Rask

## What's next

The vehicles.yaml still has placeholder values for monthly_set_aside on PTJ029 and MSA52U — updating those to the computed deposit amounts would close that loop. After that, the financials project can be turned toward actually funding the replacement accounts.
