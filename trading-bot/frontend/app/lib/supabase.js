import { createClient } from "@supabase/supabase-js";

const supabaseUrl = "https://jzwywprcogrnmjhkjnfq.supabase.co";
const supabaseKey = "sb_publishable_ar_645pU-xSHFt_X6MMRNw_dIcICpBG";

export const supabase = createClient(supabaseUrl, supabaseKey);
