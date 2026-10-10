import app.freerouting.board.facade.RoutingBoard;
import app.freerouting.board.trace.PolylineTrace;
import app.freerouting.board.model.items.*;
import app.freerouting.geometry.planar.*;
import app.freerouting.io.BoardReadResult;
import app.freerouting.io.CoordinateTransform;
import app.freerouting.io.specctra.DsnReader;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Whole-DSN import/contact observation only; never invokes a routing operation. */
public final class AreaContactProbe {
    static final String[] CASES={"front0-positive","front0-false_hull","front0-foreign_intrusion","back90-positive","back90-false_hull","back90-foreign_intrusion"};
    static Map<String,Object> map(Object... pairs) {
        Map<String,Object> m = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) m.put((String)pairs[i], pairs[i+1]);
        return m;
    }

    static String json(Object v) {
        if (v == null) return "null";
        if (v instanceof String s) {
            StringBuilder b = new StringBuilder("\"");
            for (char c : s.toCharArray()) {
                if (c == '"' || c == '\\') b.append('\\').append(c);
                else if (c < 32) b.append(String.format("\\u%04x", (int)c));
                else b.append(c);
            }
            return b.append('"').toString();
        }
        if (v instanceof Boolean) return v.toString();
        if (v instanceof Number n) {
            if (!Double.isFinite(n.doubleValue())) throw new IllegalArgumentException("nonfinite observation");
            return v.toString();
        }
        if (v instanceof Map<?,?> m) {
            List<String> entries = new ArrayList<>();
            for (var e : m.entrySet()) entries.add(json(e.getKey()) + ":" + json(e.getValue()));
            return "{" + String.join(",", entries) + "}";
        }
        if (v instanceof List<?> l) {
            List<String> items = new ArrayList<>();
            for (Object item : l) items.add(json(item));
            return "[" + String.join(",", items) + "]";
        }
        throw new IllegalArgumentException("unexpected JSON type");
    }

    static String sha(byte[] raw) throws Exception {
        return java.util.HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }

    static List<Object> point(CoordinateTransform ct, FloatPoint p) {
        double[] q=ct.boardToDsn(p);return List.of(q[0],q[1]);
    }
    static List<Object> box(CoordinateTransform ct, IntBox b) {
        double[] a=ct.boardToDsn(b.ll.toFloat()),z=ct.boardToDsn(b.ur.toFloat());
        return List.of(a[0],a[1],z[0],z[1]);
    }
    static Object integerPoint(Point p) {
        if(p instanceof IntPoint ip)return List.of(ip.x,ip.y);
        return null; // Retain actual unsupported rational class, never silently round it.
    }
    static List<Integer> ids(Collection<Item> items) {
        if(items.size()>64)throw new IllegalArgumentException("contact population bound");
        List<Integer> result=new ArrayList<>();for(Item item:items)result.add(item.getId());
        Collections.sort(result);return result;
    }
    static Map<String,Object> common(Item item,RoutingBoard board) {
        if(item.netCount()!=1)throw new IllegalArgumentException("single explicit item net required");
        int net=item.getNetNumber(0);
        return map("id",item.getId(),"net",board.rules.nets.get(net).name,
          "fixed",item.getFixedState().name(),"clearance_class_index",item.clearanceClassIndex(),
          "contacts",ids(item.getNormalContacts()),"connected",ids(item.getConnectedSet(net)));
    }
    static void observe(RoutingBoard board,String mode,Map<String,Object> state) {
        CoordinateTransform ct=board.communication.coordinateTransform;
        var counts=map("pins",board.getPins().size(),"traces",board.getTraces().size(),"areas",board.getConductionAreas().size(),
          "vias",board.getVias().size(),"components",board.components.count(),"layers",board.getLayerCount(),"max_net_number",board.rules.nets.maxNetNumber());
        state.putAll(map("mode",mode,"census",counts,"ignore_conduction",board.rules.getIgnoreConduction(),
          "board_units_per_um",ct.dsnToBoard(1.0),"board_origin_dsn_um",point(ct,new FloatPoint(0,0))));
        if(board.getPins().size()>16||board.getTraces().size()>32||board.getConductionAreas().size()>8
           ||board.getVias().size()>8||board.components.count()>16||board.getLayerCount()>8||board.rules.nets.maxNetNumber()>8)
           throw new IllegalArgumentException("imported population above observation bound; actual census retained");
        List<Object> pins=new ArrayList<>(),areas=new ArrayList<>(),traces=new ArrayList<>(),nets=new ArrayList<>();
        state.putAll(map("pins",pins,"areas",areas,"traces",traces,"nets",nets));
        for(Pin pin:board.getPins()) {
            var row=common(pin,board);List<String> layers=new ArrayList<>();
            for(int l=0;l<board.getLayerCount();l++)if(pin.isOnLayer(l))layers.add(board.layerStructure.layers[l].name);
            row.putAll(map("reference",pin.componentName(),"number",pin.name(),"position_um",point(ct,pin.getCenter().toFloat()),
              "bounds_um",box(ct,pin.boundingBox()),"layers",layers,"padstack_name",pin.getPadstack().name));pins.add(row);
        }
        for(ConductionArea a:board.getConductionAreas()) {
            var row=common(a,board);Area shape=a.getArea();var pts=shape.cornerApproxArr();
            if(pts.length<3||pts.length>16)throw new IllegalArgumentException("bounded area contour required");
            List<Object> ring=new ArrayList<>(),integerRing=new ArrayList<>();List<String> ringClasses=new ArrayList<>();
            if(!(shape.getBorder() instanceof PolylineShape border))throw new IllegalArgumentException("nonpolyline area border");
            if(border.borderLineCount()!=pts.length)throw new IllegalArgumentException("border corner count mismatch");
            for(int k=0;k<pts.length;k++){Point pt=border.corner(k);ring.add(point(ct,pt.toFloat()));integerRing.add(integerPoint(pt));ringClasses.add(pt.getClass().getName());}
            double scale=ct.boardToDsn(1.0);
            row.putAll(map("ring_um",ring,"ring_board_integer",integerRing,"ring_classes",ringClasses,"area_um2",shape.getBorder().area()*scale*scale,"holes",shape.getHoles().length,
              "layer",board.layerStructure.layers[a.getLayer()].name,"obstacle",a.getIsObstacle()));areas.add(row);
        }
        for(Trace t:board.getTraces()) {
            var row=common(t,board);traces.add(row);boolean clear=true;
            if(!(t instanceof PolylineTrace poly))throw new IllegalArgumentException("unobserved trace subtype "+t.getClass().getName());
            int n=poly.cornerCount();row.put("corner_count",n);
            if(n<2||n>32)throw new IllegalArgumentException("trace full corner population bound");
            List<Object> corners=new ArrayList<>(),integerCorners=new ArrayList<>();List<String> cornerClasses=new ArrayList<>();
            for(int k=0;k<n;k++){Point pt=poly.polyline().corner(k);corners.add(point(ct,pt.toFloat()));integerCorners.add(integerPoint(pt));cornerClasses.add(pt.getClass().getName());}
            row.putAll(map("corners_um",corners,"corners_board_integer",integerCorners,"corner_classes",cornerClasses));
            Map<String,Object> clearance=new LinkedHashMap<>();
            for(ConductionArea a:board.getConductionAreas())clearance.put(Integer.toString(a.getId()),ct.boardToDsn(board.clearanceValue(a.clearanceClassIndex(),t.clearanceClassIndex(),t.getLayer())));
            row.put("area_clearances_um",clearance);Set<Integer> overlap=new TreeSet<>();
            int count=t.tileShapeCount();if(count<1||count>32)throw new IllegalArgumentException("trace shape bound");
            for(int i=0;i<count;i++) {
                TileShape shape=t.getTileShape(i);
                clear &=board.checkTraceShape(shape,t.getLayer(),new int[]{t.getNetNumber(0)},t.clearanceClassIndex(),null);
                for(Item other:board.overlappingItemsWithClearance(shape,t.getLayer(),new int[]{t.getNetNumber(0)},t.clearanceClassIndex()))
                    overlap.add(other.getId());
            }
            row.putAll(map("start_um",point(ct,t.firstCorner().toFloat()),"end_um",point(ct,t.lastCorner().toFloat()),
              "width_um",ct.boardToDsn(2.0*t.getHalfWidth()),"layer",board.layerStructure.layers[t.getLayer()].name,
              "tree_trace_check_clear",clear,"tree_overlap_ids",new ArrayList<>(overlap)));
        }
        if(board.rules.nets.maxNetNumber()>8)throw new IllegalArgumentException("net bound");
        for(int i=1;i<=board.rules.nets.maxNetNumber();i++) {
            var n=board.rules.nets.get(i);if(n==null)continue;
            List<Object> sets=new ArrayList<>();for(var group:board.getConnectedSets(i))sets.add(ids(group));
            nets.add(map("name",n.name,"number",n.netNumber,"contains_plane",n.containsPlane(),
              "terminal_ids",ids(n.getTerminalItems()),"connected_sets",sets,
              "trace_width_um",ct.boardToDsn(2.0*board.rules.getTraceHalfWidth(i,board.getPins().iterator().next().firstLayer()))));
        }

    }
    static void runCase(Path input,String name,Map<String,Object> row) throws Exception {
        if(Files.isSymbolicLink(input)||!Files.isRegularFile(input))throw new IllegalArgumentException("regular input required");
        byte[] raw;try(InputStream s=Files.newInputStream(input)){raw=s.readNBytes(16385);}
        if(raw.length==0||raw.length>16384)throw new IllegalArgumentException("input bound");
        row.putAll(map("input_sha256",sha(raw),"status","importing","routing_executed",false));
        BoardReadResult result=DsnReader.readBoard(new ByteArrayInputStream(raw),null,null);
        row.put("parser_result_class",result.getClass().getName());
        if(!(result instanceof BoardReadResult.Success success))throw new IllegalArgumentException("import result "+result);
        row.put("parser_warnings",success.warnings());
        if(!(success.board() instanceof RoutingBoard board))throw new IllegalArgumentException("RoutingBoard required");
        board.awaitPostLoad();
        List<Object> states=new ArrayList<>();row.put("states",states);
        for(String mode:List.of("imported","obstacle_false","obstacle_true")){
            if(!mode.equals("imported"))board.changePlaneAsObstacle(mode.equals("obstacle_true"));
            var state=map("mode",mode);states.add(state);observe(board,mode,state);
        }
        row.put("status","observed");
    }
    static void save(Path target,Map<String,Object> result) throws Exception {
        byte[] raw=(json(result)+"\n").getBytes(StandardCharsets.UTF_8);
        if(raw.length>262144)throw new IllegalArgumentException("observation output bound");
        Path partial=target.resolveSibling(target.getFileName()+".partial");Files.write(partial,raw);
        Files.move(partial,target,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("input-directory output-json");
        Path in=Path.of(args[0]),out=Path.of(args[1]);if(Files.exists(out))throw new IllegalArgumentException("fresh output required");
        List<Object> rows=new ArrayList<>();for(String c:CASES)rows.add(map("case",c,"status","not_run"));
        var result=map("schema",1,"scope","owned_area_contact_import_only","units","micrometres",
          "routing_executed",false,"native_executed",false,"cases",rows);save(out,result);boolean complete=true;
        for(int i=0;i<CASES.length;i++){
            Map<String,Object> row=map("case",CASES[i],"status","starting");rows.set(i,row);
            try{runCase(in.resolve(CASES[i]+".dsn"),CASES[i],row);}
            catch(Exception e){complete=false;String s=e.getClass().getName()+": "+e.getMessage();row.putAll(map("status","failed","error",s.substring(0,Math.min(1024,s.length()))));}
            save(out,result);
        }
        if(!complete)System.exit(2);
    }
}
