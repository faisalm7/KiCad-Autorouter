package app.freerouting.geometry.planar;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;

/** Exact bounded observation of the pinned engine's projective coordinates, not acceptance. */
public final class ExactPointWitness {
  private ExactPointWitness() {}
  public static Map<String,String> capture(Point point) {
    BigInteger x,y,z;
    if(point!=null&&point.getClass()==IntPoint.class){
      IntPoint p=(IntPoint)point;
      x=BigInteger.valueOf(p.x);y=BigInteger.valueOf(p.y);z=BigInteger.ONE;
    }else if(point!=null&&point.getClass()==RationalPoint.class){
      // Same-package access: pinned RationalPoint stores affine coordinates as (x/z,y/z).
      RationalPoint p=(RationalPoint)point;x=p.x;y=p.y;z=p.z;
    }else throw new IllegalArgumentException("unsupported exact point class");
    if(x==null||y==null||z==null||z.signum()<=0
        ||x.abs().bitLength()>4096||y.abs().bitLength()>4096||z.bitLength()>4096)
      throw new IllegalArgumentException("nonfinite or oversized exact point");
    BigInteger gcd=x.abs().gcd(y.abs()).gcd(z);
    Map<String,String> result=new LinkedHashMap<>();
    result.put("x",x.divide(gcd).toString());result.put("y",y.divide(gcd).toString());
    result.put("z",z.divide(gcd).toString());return result;
  }
}
